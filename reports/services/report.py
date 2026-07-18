"""Store reporting service."""

from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from accounts.enums import MembershipStatus
from accounts.models import StoreMembership
from core.cache import cache_manager
from core.cache.keys import report_sales, report_summary
from orders.enums import OrderStatus, ShipmentStatus
from orders.models import Order, OrderItem, Shipment
from payments.enums import PaymentStatus
from payments.models import PaymentTransaction
from products.models import Inventory, Product
from products.enums import ProductStatus

PAID_ORDER_STATUSES = [
    OrderStatus.PAID,
    OrderStatus.PREPARING,
    OrderStatus.SENT,
    OrderStatus.DELIVERED,
]


class ReportService:
    """Aggregate store analytics across sales, customers, products, inventory, payments, shipping."""

    def _since(self, days: int):
        return timezone.now() - timedelta(days=days)

    def get_summary(self, store, days: int = 30) -> dict:
        cache_key = report_summary(store.id, days)
        return cache_manager.get_or_set(
            cache_key,
            lambda: self._build_summary(store, days),
            ttl="reports",
        )

    def _build_summary(self, store, days: int = 30) -> dict:
        sales = self.get_sales_report(store, days)
        customers = self.get_customers_report(store, days)
        return {
            "period_days": days,
            "new_customers": customers["new_customers"],
            "total_customers": customers["total_customers"],
            "total_orders": sales["total_orders"],
            "total_revenue": sales["total_revenue"],
            "top_products": sales["top_products"][:5],
            "orders_by_status": sales["orders_by_status"],
            "message": "",
        }

    def get_sales_report(self, store, days: int = 30) -> dict:
        cache_key = report_sales(store.id, days)
        return cache_manager.get_or_set(
            cache_key,
            lambda: self._build_sales_report(store, days),
            ttl="reports",
        )

    def _build_sales_report(self, store, days: int = 30) -> dict:
        since = self._since(days)
        orders = Order.objects.filter(store=store, created_at__gte=since)
        paid_orders = orders.filter(status__in=PAID_ORDER_STATUSES)

        by_status = dict(orders.values("status").annotate(c=Count("id")).values_list("status", "c"))
        revenue = paid_orders.aggregate(total=Sum("total"))["total"] or 0
        paid_count = paid_orders.count()
        average_order_value = int(revenue / paid_count) if paid_count else 0

        daily = (
            paid_orders.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(orders=Count("id"), revenue=Sum("total"))
            .order_by("day")
        )

        top_products = (
            OrderItem.objects.filter(order__store=store, order__created_at__gte=since)
            .values("product_id", "product_name")
            .annotate(quantity=Sum("quantity"), revenue=Sum("line_total"))
            .order_by("-revenue")[:10]
        )

        return {
            "period_days": days,
            "total_orders": orders.count(),
            "paid_orders": paid_count,
            "total_revenue": int(revenue),
            "average_order_value": average_order_value,
            "total_discount": int(orders.aggregate(d=Sum("discount"))["d"] or 0),
            "total_tax": int(orders.aggregate(t=Sum("tax"))["t"] or 0),
            "total_shipping": int(orders.aggregate(s=Sum("shipping_cost"))["s"] or 0),
            "orders_by_status": {
                status: by_status.get(status, 0)
                for status in OrderStatus.values
            },
            "daily_sales": [
                {
                    "date": row["day"].isoformat() if row["day"] else "",
                    "orders": row["orders"],
                    "revenue": int(row["revenue"] or 0),
                }
                for row in daily
            ],
            "top_products": [
                {
                    "product_id": row["product_id"],
                    "name": row["product_name"],
                    "quantity": row["quantity"],
                    "revenue": int(row["revenue"] or 0),
                }
                for row in top_products
            ],
        }

    def get_customers_report(self, store, days: int = 30) -> dict:
        since = self._since(days)
        memberships = StoreMembership.objects.filter(store=store, role__codename="customer")
        new_customers = memberships.filter(created_at__gte=since).count()

        active = memberships.filter(status=MembershipStatus.ACTIVE).count()
        top_customers = (
            Order.objects.filter(store=store, created_at__gte=since, status__in=PAID_ORDER_STATUSES)
            .values("user_id", "user__phone", "user__first_name", "user__last_name")
            .annotate(orders=Count("id"), spent=Sum("total"))
            .order_by("-spent")[:10]
        )

        return {
            "period_days": days,
            "total_customers": memberships.count(),
            "new_customers": new_customers,
            "active_customers": active,
            "inactive_customers": memberships.filter(status=MembershipStatus.INACTIVE).count(),
            "top_customers": [
                {
                    "user_id": row["user_id"],
                    "phone": row["user__phone"] or "",
                    "full_name": f"{row['user__first_name'] or ''} {row['user__last_name'] or ''}".strip(),
                    "orders": row["orders"],
                    "spent": int(row["spent"] or 0),
                }
                for row in top_customers
                if row["user_id"]
            ],
        }

    def get_products_report(self, store, days: int = 30) -> dict:
        since = self._since(days)
        products = Product.objects.filter(store=store)
        active_count = products.filter(status=ProductStatus.ACTIVE).count()

        sold = (
            OrderItem.objects.filter(order__store=store, order__created_at__gte=since)
            .values("product_id")
            .annotate(sold_qty=Sum("quantity"), revenue=Sum("line_total"))
        )
        sold_map = {row["product_id"]: row for row in sold}

        top_selling = sorted(
            [
                {
                    "product_id": pid,
                    "name": products.filter(pk=pid).values_list("name", flat=True).first() or "",
                    "sold_quantity": row["sold_qty"],
                    "revenue": int(row["revenue"] or 0),
                }
                for pid, row in sold_map.items()
            ],
            key=lambda x: x["revenue"],
            reverse=True,
        )[:10]

        unsold_active = products.filter(status=ProductStatus.ACTIVE).exclude(
            pk__in=sold_map.keys(),
        ).count()

        return {
            "period_days": days,
            "total_products": products.count(),
            "active_products": active_count,
            "draft_products": products.filter(status=ProductStatus.DRAFT).count(),
            "sold_products": len(sold_map),
            "unsold_active_products": unsold_active,
            "top_selling": top_selling,
        }

    def get_inventory_report(self, store) -> dict:
        items = Inventory.objects.filter(product__store=store).select_related("product", "variant")
        low_stock = []
        out_of_stock = []
        total_units = 0

        for item in items:
            if not item.track_inventory:
                continue
            available = item.available
            total_units += available
            label = item.product.name if item.product_id else str(item.variant)
            entry = {
                "product_id": item.product_id,
                "variant_id": item.variant_id,
                "name": label,
                "quantity": item.quantity,
                "reserved": item.reserved,
                "available": available,
            }
            if available <= 0:
                out_of_stock.append(entry)
            elif item.is_low_stock:
                low_stock.append(entry)

        return {
            "tracked_items": items.filter(track_inventory=True).count(),
            "total_available_units": total_units,
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock),
            "low_stock_items": low_stock[:20],
            "out_of_stock_items": out_of_stock[:20],
        }

    def get_payments_report(self, store, days: int = 30) -> dict:
        since = self._since(days)
        payments = PaymentTransaction.objects.filter(store=store, created_at__gte=since)

        by_status = dict(payments.values("status").annotate(c=Count("id")).values_list("status", "c"))
        by_gateway = (
            payments.values("gateway")
            .annotate(count=Count("id"), amount=Sum("amount"))
            .order_by("-amount")
        )

        successful = payments.filter(status=PaymentStatus.PAID)
        failed = payments.filter(status=PaymentStatus.FAILED)

        return {
            "period_days": days,
            "total_transactions": payments.count(),
            "successful_count": successful.count(),
            "failed_count": failed.count(),
            "total_paid_amount": int(successful.aggregate(t=Sum("amount"))["t"] or 0),
            "total_refunded": int(payments.aggregate(r=Sum("refunded_amount"))["r"] or 0),
            "by_status": {status: by_status.get(status, 0) for status in PaymentStatus.values},
            "by_gateway": [
                {
                    "gateway": row["gateway"],
                    "count": row["count"],
                    "amount": int(row["amount"] or 0),
                }
                for row in by_gateway
            ],
        }

    def get_shipping_report(self, store, days: int = 30) -> dict:
        since = self._since(days)
        shipments = Shipment.objects.filter(order__store=store, created_at__gte=since)

        by_status = dict(shipments.values("status").annotate(c=Count("id")).values_list("status", "c"))
        delivered = shipments.filter(status=ShipmentStatus.DELIVERED).count()
        pending = shipments.filter(status=ShipmentStatus.PENDING).count()

        shipping_revenue = (
            Order.objects.filter(store=store, created_at__gte=since, status__in=PAID_ORDER_STATUSES)
            .aggregate(total=Sum("shipping_cost"))["total"]
            or 0
        )

        by_carrier = (
            shipments.exclude(carrier="")
            .values("carrier")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return {
            "period_days": days,
            "total_shipments": shipments.count(),
            "delivered": delivered,
            "pending": pending,
            "shipping_revenue": int(shipping_revenue),
            "by_status": {status: by_status.get(status, 0) for status in ShipmentStatus.values},
            "by_carrier": [{"carrier": row["carrier"], "count": row["count"]} for row in by_carrier],
        }
