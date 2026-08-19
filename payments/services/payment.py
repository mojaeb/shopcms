"""Payment service layer."""

import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from carts.services.cart import CartService
from taxes.services.tax import TaxService
from payments.enums import GatewayType, PaymentStatus
from payments.models import PaymentTransaction
from payments.providers.registry import get_gateway

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    pass


class PaymentService:
    """Orchestrate payment create, verify, refund, and webhooks."""

    def __init__(self):
        self.cart_service = CartService()
        self.tax_service = TaxService()

    def get_store_gateways(self, store) -> list[dict]:
        settings = self._get_payment_settings(store)
        enabled = settings.get("gateways", [])
        default = settings.get("default_gateway", "")
        result = []
        for codename in enabled:
            gateway = get_gateway(codename)
            if not gateway:
                continue
            config = settings.get(codename, {})
            result.append({
                "codename": codename,
                "label": gateway.label,
                "is_default": codename == default,
                "implemented": gateway.is_live_ready(config),
            })
        return result

    def get_gateway_config(self, store, gateway: str) -> dict:
        settings = self._get_payment_settings(store)
        return settings.get(gateway, {"sandbox": True})

    def create_payment(
        self,
        store,
        user,
        gateway: str,
        address_id: int,
        shipping_method_id: int,
        shipping_price: Decimal,
        request,
    ) -> PaymentTransaction:
        if gateway not in dict(GatewayType.choices):
            raise PaymentError("درگاه نامعتبر است")

        enabled = [g["codename"] for g in self.get_store_gateways(store)]
        if gateway not in enabled:
            raise PaymentError("درگاه فعال نیست")

        cart = self.cart_service.get_or_create_cart(store, request)
        totals = self.cart_service.calculate_totals(cart)
        if totals["item_count"] == 0:
            raise PaymentError("سبد خرید خالی است")

        tax_result = self.tax_service.calculate_for_cart(store, cart, shipping_price)
        tax_amount = Decimal(tax_result["tax"])
        amount = totals["total"] + shipping_price + tax_amount
        if amount <= 0:
            raise PaymentError("مبلغ پرداخت نامعتبر است")

        provider = get_gateway(gateway)
        if not provider:
            raise PaymentError("درگاه یافت نشد")

        config = self.get_gateway_config(store, gateway)
        callback_url = self._build_callback_url(request, gateway)

        fail_message = None
        with transaction.atomic():
            txn = PaymentTransaction.objects.create(
                store=store,
                user=user,
                gateway=gateway,
                amount=amount,
                status=PaymentStatus.PENDING,
                callback_url=callback_url,
                metadata={
                    "address_id": address_id,
                    "shipping_method_id": shipping_method_id,
                    "shipping_price": str(shipping_price),
                    "subtotal": str(totals["subtotal"]),
                    "discount": str(totals["discount"]),
                    "tax": str(tax_amount),
                    "cart_id": cart.id,
                },
            )

            try:
                result = provider.create_payment(txn, config, callback_url)
            except (ValueError, NotImplementedError) as exc:
                txn.status = PaymentStatus.FAILED
                txn.error_message = str(exc)
                txn.save(update_fields=["status", "error_message", "updated_at"])
                fail_message = str(exc)
            else:
                txn.authority = result.authority
                txn.payment_url = result.payment_url
                txn.status = PaymentStatus.REDIRECTED
                txn.save(update_fields=["authority", "payment_url", "status", "updated_at"])
                return txn

        raise PaymentError(fail_message)

    @transaction.atomic
    def verify_payment(self, transaction: PaymentTransaction, params: dict) -> PaymentTransaction:
        if transaction.status == PaymentStatus.PAID:
            return transaction

        provider = get_gateway(transaction.gateway)
        if not provider:
            raise PaymentError("درگاه یافت نشد")

        config = self.get_gateway_config(transaction.store, transaction.gateway)
        result = provider.verify_payment(transaction, config, params)

        if result.success:
            transaction.status = PaymentStatus.PAID
            transaction.ref_id = result.ref_id
            transaction.verify_data = result.raw or params
            transaction.paid_at = timezone.now()
            transaction.error_message = ""
            transaction.save(update_fields=["status", "ref_id", "verify_data", "paid_at", "error_message", "updated_at"])
            self._create_order_from_payment(transaction)
            logger.info("Payment verified: %s", transaction.tracking_code)
        else:
            transaction.status = PaymentStatus.FAILED
            transaction.error_message = result.message or "تایید پرداخت ناموفق"
            transaction.verify_data = result.raw or params
            transaction.save(update_fields=["status", "error_message", "verify_data", "updated_at"])

        return transaction

    @transaction.atomic
    def refund_payment(self, transaction: PaymentTransaction, amount: Decimal | None = None) -> PaymentTransaction:
        if transaction.status != PaymentStatus.PAID:
            raise PaymentError("فقط پرداخت‌های موفق قابل بازگشت هستند")

        refund_amount = amount or (transaction.amount - transaction.refunded_amount)
        if refund_amount <= 0:
            raise PaymentError("مبلغ بازگشت نامعتبر است")

        provider = get_gateway(transaction.gateway)
        config = self.get_gateway_config(transaction.store, transaction.gateway)
        result = provider.refund_payment(transaction, config, refund_amount)
        if not result.success:
            raise PaymentError(result.message or "بازگشت وجه ناموفق")

        transaction.refunded_amount += result.refunded_amount
        if transaction.refunded_amount >= transaction.amount:
            transaction.status = PaymentStatus.REFUNDED
        transaction.save(update_fields=["refunded_amount", "status", "updated_at"])
        return transaction

    def handle_webhook(self, store, gateway: str, payload: dict) -> PaymentTransaction | None:
        provider = get_gateway(gateway)
        if not provider:
            return None

        parsed = provider.parse_webhook(payload)
        authority = parsed.get("Authority") or parsed.get("authority") or parsed.get("id")
        if not authority:
            return None

        txn = PaymentTransaction.objects.filter(store=store, gateway=gateway, authority=authority).first()
        if not txn:
            return None

        return self.verify_payment(txn, parsed)

    def reconcile_pending_payments(self, *, minutes: int = 30, store=None, dry_run: bool = False) -> dict:
        """Inquiry redirected Zarinpal txns older than `minutes` and verify if paid."""
        from datetime import timedelta

        from django.db.models import Q

        cutoff = timezone.now() - timedelta(minutes=minutes)
        qs = PaymentTransaction.objects.filter(
            gateway=GatewayType.ZARINPAL,
            status=PaymentStatus.REDIRECTED,
            created_at__lte=cutoff,
        ).exclude(Q(authority="") | Q(authority__isnull=True)).select_related("store")
        if store is not None:
            qs = qs.filter(store=store)

        stats = {"checked": 0, "verified": 0, "skipped": 0, "failed": 0}
        for txn in qs:
            stats["checked"] += 1
            provider = get_gateway(txn.gateway)
            if not provider or not hasattr(provider, "inquiry_payment"):
                stats["skipped"] += 1
                continue

            config = self.get_gateway_config(txn.store, txn.gateway)
            inquiry = provider.inquiry_payment(txn, config)
            if not inquiry.success:
                stats["skipped"] += 1
                logger.info(
                    "Payment inquiry not paid: %s status=%s msg=%s",
                    txn.tracking_code,
                    inquiry.status,
                    inquiry.message,
                )
                continue

            if dry_run:
                stats["verified"] += 1
                continue

            try:
                updated = self.verify_payment(
                    txn,
                    {"Authority": txn.authority, "Status": "OK"},
                )
            except PaymentError as exc:
                stats["failed"] += 1
                logger.warning("Reconcile verify failed for %s: %s", txn.tracking_code, exc)
                continue

            if updated.status == PaymentStatus.PAID:
                stats["verified"] += 1
            else:
                stats["failed"] += 1
        return stats

    def serialize_transaction(self, txn: PaymentTransaction) -> dict:
        order = getattr(txn, "order", None)
        return {
            "id": txn.id,
            "tracking_code": txn.tracking_code,
            "gateway": txn.gateway,
            "amount": str(int(txn.amount)),
            "status": txn.status,
            "payment_url": txn.payment_url,
            "ref_id": txn.ref_id,
            "paid_at": txn.paid_at.isoformat() if txn.paid_at else None,
            "metadata": txn.metadata,
            "order_id": order.id if order else txn.metadata.get("order_id"),
            "order_number": order.order_number if order else txn.metadata.get("order_number"),
        }

    def _create_order_from_payment(self, transaction: PaymentTransaction) -> None:
        from orders.services.order import OrderError, OrderService

        try:
            OrderService().create_from_payment(transaction)
        except OrderError as exc:
            logger.error("Order creation failed for payment %s: %s", transaction.tracking_code, exc)

    def _get_payment_settings(self, store) -> dict:
        from dashboard.services.store_admin import StoreAdminService

        settings = StoreAdminService()._get_group_settings(store, "payment")
        defaults = {
            "gateways": [],
            "default_gateway": "",
            "callback_base_url": "",
            "zarinpal": {
                "merchant_id": "",
                "sandbox": True,
                "api_base": "",
                "start_pay_url": "",
                "graphql_url": "",
                "access_token": "",
            },
            "idpay": {"api_key": "", "sandbox": True},
            "mellat": {"terminal_id": "", "sandbox": True},
            "pasargad": {"merchant_code": "", "sandbox": True},
            "sina": {"terminal_id": "", "sandbox": True},
        }
        return {**defaults, **settings}

    def _build_callback_url(self, request, gateway: str) -> str:
        # Prefer payment.callback_base_url when set (public domain / reverse proxy).
        store = getattr(request, "store", None)
        if store is None:
            from tenants.context import get_current_store

            store = get_current_store()
        if store is not None:
            base = str(self._get_payment_settings(store).get("callback_base_url") or "").strip().rstrip("/")
            if base:
                return f"{base}/api/v1/payments/callback/{gateway}/"
        host = request.get_host()
        scheme = "https" if request.is_secure() else "http"
        return f"{scheme}://{host}/api/v1/payments/callback/{gateway}/"
