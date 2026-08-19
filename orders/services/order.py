"""Order service layer."""

import logging
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from addresses.models import CustomerAddress
from addresses.services.address import AddressService
from carts.models import Cart
from carts.services.cart import CartService
from notifications.services.notification import NotificationError, NotificationService
from orders.enums import OrderStatus, ShipmentStatus
from orders.models import Invoice, Order, OrderHistory, OrderItem, Shipment, generate_order_number
from payments.models import PaymentTransaction
from shipping.models import ShippingMethod

logger = logging.getLogger(__name__)

_notification_service = NotificationService()


class OrderError(Exception):
    pass


class OrderService:
    """Create and manage customer orders."""

    def __init__(self):
        self.cart_service = CartService()
        self.address_service = AddressService()

    @transaction.atomic
    def create_from_payment(self, payment: PaymentTransaction) -> Order:
        existing = Order.objects.filter(payment=payment).first()
        if existing:
            return existing

        metadata = payment.metadata or {}
        cart_id = metadata.get("cart_id")
        cart = Cart.objects.filter(pk=cart_id, store=payment.store).first() if cart_id else None
        if not cart:
            raise OrderError("سبد خرید برای ثبت سفارش یافت نشد")

        address_snapshot = self._resolve_address_snapshot(payment, metadata)
        shipping_method = self._resolve_shipping_method(payment.store, metadata)

        subtotal = Decimal(str(metadata.get("subtotal", "0")))
        discount = Decimal(str(metadata.get("discount", "0")))
        shipping_cost = Decimal(str(metadata.get("shipping_price", "0")))
        tax = Decimal(str(metadata.get("tax", "0")))
        total = subtotal - discount + shipping_cost + tax

        order_number = generate_order_number()
        while Order.objects.filter(store=payment.store, order_number=order_number).exists():
            order_number = generate_order_number()

        order = Order.objects.create(
            store=payment.store,
            user=payment.user,
            order_number=order_number,
            status=OrderStatus.PAID,
            payment=payment,
            address_snapshot=address_snapshot,
            shipping_method=shipping_method.name if shipping_method else "",
            shipping_provider=shipping_method.provider if shipping_method else "",
            subtotal=subtotal,
            discount=discount,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total,
            coupon_code=cart.coupon.code if cart.coupon_id else "",
            gift_card_code=cart.gift_card.code if cart.gift_card_id else "",
        )

        items = cart.items.select_related("product", "variant").prefetch_related("variant__attributes__attribute")
        for item in items:
            OrderItem.objects.create(
                order=order,
                product_id=item.product_id,
                product_name=item.product.name,
                product_slug=item.product.slug,
                variant_id=item.variant_id,
                variant_label=self.cart_service._variant_label(item.variant) if item.variant_id else "",
                sku=item.variant.sku if item.variant_id else item.product.sku,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total,
                image=item.product.primary_image or "",
            )

        Shipment.objects.create(
            order=order,
            status=ShipmentStatus.PENDING,
            carrier=shipping_method.name if shipping_method else "",
            metadata={"shipping_method_id": metadata.get("shipping_method_id")},
        )

        OrderHistory.objects.create(
            order=order,
            status=OrderStatus.PAID,
            note="سفارش پس از پرداخت موفق ثبت شد",
            created_by=payment.user,
        )

        Invoice.objects.create(
            order=order,
            invoice_number=f"INV-{order.order_number}",
        )

        from carts.services.discount import DiscountService

        DiscountService().redeem_on_order(order, cart, payment.user)

        self.cart_service.clear_cart(cart)

        from digital.services.digital import DigitalService

        DigitalService().issue_licenses_for_order(order)

        from subscriptions.services.subscription import SubscriptionService

        SubscriptionService().create_from_order(order)

        payment.metadata = {**metadata, "order_id": order.id, "order_number": order.order_number}
        payment.save(update_fields=["metadata", "updated_at"])

        logger.info("Order created from payment: %s -> %s", payment.tracking_code, order.order_number)
        return order

    @transaction.atomic
    def update_status(
        self,
        order: Order,
        new_status: str,
        note: str = "",
        user=None,
    ) -> Order:
        if new_status not in OrderStatus.values:
            raise OrderError("وضعیت نامعتبر است")

        old_status = order.status
        if old_status == new_status:
            return order

        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        OrderHistory.objects.create(
            order=order,
            status=new_status,
            note=note or f"تغییر وضعیت از {old_status} به {new_status}",
            created_by=user if getattr(user, "pk", None) else None,
        )

        shipment = getattr(order, "shipment", None)
        if shipment:
            if new_status == OrderStatus.PREPARING:
                shipment.status = ShipmentStatus.PREPARING
                shipment.save(update_fields=["status", "updated_at"])
            elif new_status == OrderStatus.SENT:
                old_shipment_status = shipment.status
                shipment.status = ShipmentStatus.SHIPPED
                shipment.shipped_at = timezone.now()
                shipment.save(update_fields=["status", "shipped_at", "updated_at"])
                if old_shipment_status != ShipmentStatus.SHIPPED:
                    self._notify_shipment_status(order, shipment)
            elif new_status == OrderStatus.DELIVERED:
                old_shipment_status = shipment.status
                shipment.status = ShipmentStatus.DELIVERED
                shipment.delivered_at = timezone.now()
                shipment.save(update_fields=["status", "delivered_at", "updated_at"])
                if old_shipment_status != ShipmentStatus.DELIVERED:
                    self._notify_shipment_status(order, shipment)

        return order

    @transaction.atomic
    def update_shipment(
        self,
        order: Order,
        tracking_code: str = "",
        carrier: str = "",
        status: str | None = None,
    ) -> Shipment:
        shipment, _ = Shipment.objects.get_or_create(
            order=order,
            defaults={"status": ShipmentStatus.PENDING},
        )
        old_status = shipment.status
        if tracking_code:
            shipment.tracking_code = tracking_code
        if carrier:
            shipment.carrier = carrier
        if status and status in ShipmentStatus.values:
            shipment.status = status
            if status == ShipmentStatus.SHIPPED and not shipment.shipped_at:
                shipment.shipped_at = timezone.now()
            if status == ShipmentStatus.DELIVERED and not shipment.delivered_at:
                shipment.delivered_at = timezone.now()
        shipment.save()
        if shipment.status != old_status and shipment.status in (ShipmentStatus.SHIPPED, ShipmentStatus.DELIVERED):
            self._notify_shipment_status(order, shipment)
        return shipment

    def list_customer_orders(self, user, store):
        return Order.objects.filter(store=store, user=user).prefetch_related("items")

    def get_customer_order(self, user, store, order_id: int) -> Order:
        try:
            return Order.objects.prefetch_related("items", "history", "shipment").get(
                pk=order_id, store=store, user=user,
            )
        except Order.DoesNotExist:
            raise OrderError("سفارش یافت نشد")

    def list_store_orders(self, store, status: str | None = None):
        qs = Order.objects.filter(store=store).select_related("user", "payment").prefetch_related("items")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")

    def get_store_order(self, store, order_id: int) -> Order:
        try:
            return Order.objects.select_related("user", "payment").prefetch_related(
                "items", "history", "shipment", "invoice",
            ).get(pk=order_id, store=store)
        except Order.DoesNotExist:
            raise OrderError("سفارش یافت نشد")

    def get_store_order_stats(self, store) -> dict:
        today = timezone.now().date()
        agg = Order.objects.filter(store=store).aggregate(
            order_count=Count("id"),
            revenue=Sum("total"),
        )
        pending = Order.objects.filter(
            store=store,
            status__in=[OrderStatus.PAID, OrderStatus.PREPARING],
        ).count()
        orders_today = Order.objects.filter(store=store, created_at__date=today).count()
        return {
            "total_orders": agg["order_count"] or 0,
            "pending_orders": pending,
            "total_revenue": int(agg["revenue"] or 0),
            "orders_today": orders_today,
        }

    def get_reports_data(self, store, days: int = 30) -> dict:
        since = timezone.now() - timedelta(days=days)
        orders = Order.objects.filter(store=store, created_at__gte=since)
        by_status = dict(
            orders.values("status").annotate(c=Count("id")).values_list("status", "c")
        )
        revenue = orders.filter(status__in=[
            OrderStatus.PAID, OrderStatus.PREPARING, OrderStatus.SENT, OrderStatus.DELIVERED,
        ]).aggregate(total=Sum("total"))["total"] or 0

        top_products = (
            OrderItem.objects.filter(order__store=store, order__created_at__gte=since)
            .values("product_name")
            .annotate(qty=Sum("quantity"))
            .order_by("-qty")[:5]
        )

        return {
            "total_orders": orders.count(),
            "total_revenue": int(revenue),
            "orders_by_status": {
                status: by_status.get(status, 0)
                for status in [
                    OrderStatus.PENDING,
                    OrderStatus.PAID,
                    OrderStatus.PREPARING,
                    OrderStatus.SENT,
                    OrderStatus.DELIVERED,
                    OrderStatus.CANCELED,
                ]
            },
            "top_products": [
                {"name": row["product_name"], "quantity": row["qty"]}
                for row in top_products
            ],
        }

    def serialize_order(self, order: Order, detailed: bool = False) -> dict:
        data = {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "status_label": order.get_status_display(),
            "subtotal": str(int(order.subtotal)),
            "discount": str(int(order.discount)),
            "shipping_cost": str(int(order.shipping_cost)),
            "tax": str(int(order.tax)),
            "total": str(int(order.total)),
            "coupon_code": order.coupon_code,
            "gift_card_code": order.gift_card_code,
            "shipping_method": order.shipping_method,
            "address": order.address_snapshot,
            "item_count": sum(item.quantity for item in order.items.all()),
            "created_at": order.created_at.isoformat(),
        }

        if detailed:
            data["items"] = [self._serialize_item(item) for item in order.items.all()]
            data["customer_note"] = order.customer_note
            if hasattr(order, "shipment") and order.shipment:
                s = order.shipment
                data["shipment"] = {
                    "status": s.status,
                    "tracking_code": s.tracking_code,
                    "carrier": s.carrier,
                    "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
                    "delivered_at": s.delivered_at.isoformat() if s.delivered_at else None,
                }
            data["history"] = [
                {
                    "status": h.status,
                    "note": h.note,
                    "created_at": h.created_at.isoformat(),
                }
                for h in order.history.all()
            ]
            if hasattr(order, "invoice") and order.invoice:
                data["invoice"] = {
                    "invoice_number": order.invoice.invoice_number,
                    "issued_at": order.invoice.issued_at.isoformat(),
                    "pdf_url": order.invoice.pdf_url,
                    "pdf_available": bool(order.invoice.pdf_url),
                }
            if order.payment_id:
                data["payment"] = {
                    "tracking_code": order.payment.tracking_code,
                    "ref_id": order.payment.ref_id,
                    "gateway": order.payment.gateway,
                }
        return data

    def serialize_order_admin(self, order: Order) -> dict:
        data = self.serialize_order(order, detailed=True)
        data["user"] = {
            "id": order.user_id,
            "phone": order.user.phone if order.user_id else "",
            "full_name": order.user.full_name if order.user_id else "",
        }
        return data

    def serialize_invoice(self, order: Order) -> dict:
        invoice = getattr(order, "invoice", None)
        if not invoice:
            invoice = Invoice.objects.create(
                order=order,
                invoice_number=f"INV-{order.order_number}",
            )
        return {
            "invoice_number": invoice.invoice_number,
            "order_number": order.order_number,
            "issued_at": invoice.issued_at.isoformat(),
            "pdf_url": invoice.pdf_url,
            "pdf_available": bool(invoice.pdf_url),
            "message": "دانلود PDF در فاز بعدی فعال می‌شود" if not invoice.pdf_url else "",
            "totals": {
                "subtotal": str(int(order.subtotal)),
                "discount": str(int(order.discount)),
                "shipping_cost": str(int(order.shipping_cost)),
                "tax": str(int(order.tax)),
                "total": str(int(order.total)),
            },
            "items": [self._serialize_item(item) for item in order.items.all()],
            "address": order.address_snapshot,
        }

    def _serialize_item(self, item: OrderItem) -> dict:
        return {
            "product_id": item.product_id,
            "product_name": item.product_name,
            "product_slug": item.product_slug,
            "variant_id": item.variant_id,
            "variant_label": item.variant_label,
            "sku": item.sku,
            "quantity": item.quantity,
            "unit_price": str(int(item.unit_price)),
            "line_total": str(int(item.line_total)),
            "image": item.image,
        }

    def _shipment_sms_enabled(self, store) -> bool:
        from dashboard.services.store_admin import StoreAdminService

        settings = StoreAdminService()._get_group_settings(store, "notifications")
        return bool(settings.get("shipment_sms_enabled", False))

    def _customer_phone(self, order: Order) -> str:
        """شماره تلفن مشتری: ابتدا از snapshot آدرس، سپس از user."""
        snapshot = order.address_snapshot or {}
        phone = snapshot.get("phone", "")
        if phone:
            return str(phone)
        if order.user_id and order.user:
            return str(order.user.phone or "")
        return ""

    def _notify_shipment_status(self, order: Order, shipment: Shipment) -> None:
        """پیامک وضعیت مرسوله به مشتری — هرگز کل تراکنش را fail نمی‌کند."""
        if not self._shipment_sms_enabled(order.store):
            return
        phone = self._customer_phone(order)
        if not phone:
            logger.warning("shipment sms: no phone for order %s", order.order_number)
            return
        if shipment.status == ShipmentStatus.SHIPPED:
            tracking = shipment.tracking_code or "به‌زودی"
            body = f"سفارش {order.order_number} شما ارسال شد. کد رهگیری: {tracking}"
        elif shipment.status == ShipmentStatus.DELIVERED:
            body = f"سفارش {order.order_number} شما تحویل داده شد. متشکریم!"
        else:
            return
        try:
            _notification_service.send_sms(
                phone,
                body,
                store=order.store,
                metadata={"order_number": order.order_number, "shipment_status": shipment.status},
            )
        except NotificationError as exc:
            logger.warning("shipment sms failed for order %s: %s", order.order_number, exc)

    def _resolve_address_snapshot(self, payment: PaymentTransaction, metadata: dict) -> dict:
        address_id = metadata.get("address_id")
        if payment.user_id and address_id:
            address = CustomerAddress.objects.filter(
                pk=address_id, user=payment.user, store=payment.store,
            ).first()
            if address:
                return self.address_service.serialize_address(address)
        return metadata.get("address_snapshot", {})

    def _resolve_shipping_method(self, store, metadata: dict) -> ShippingMethod | None:
        method_id = metadata.get("shipping_method_id")
        if not method_id:
            return None
        return ShippingMethod.objects.filter(pk=method_id, store=store).first()
