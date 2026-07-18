"""Shipping service layer."""

from decimal import Decimal

from carts.services.cart import CartService
from shipping.models import ShippingMethod
from shipping.providers.base import ShippingContext, ShippingQuote
from shipping.providers.registry import get_provider


class ShippingService:
    """Quote shipping methods for a cart and destination."""

    DEFAULT_ITEM_WEIGHT_KG = Decimal("0.5")

    def get_store_origin(self, store) -> tuple[str, str]:
        from dashboard.services.store_admin import StoreAdminService

        settings = StoreAdminService()._get_group_settings(store, "shipping")
        origin = settings.get("origin", {})
        if isinstance(origin, dict):
            return origin.get("origin_city", "مشهد"), origin.get("origin_province", "خراسان رضوی")
        return settings.get("origin_city", "مشهد"), settings.get("origin_province", "خراسان رضوی")

    def build_context(self, store, province: str, city: str, cart=None, request=None) -> ShippingContext:
        if cart is None and request is not None:
            cart = CartService().get_or_create_cart(store, request)
        subtotal = Decimal("0")
        item_count = 0
        weight_kg = Decimal("0")
        if cart:
            totals = CartService().calculate_totals(cart)
            subtotal = totals["subtotal"]
            for item in cart.items.select_related("product"):
                item_count += item.quantity
                weight_kg += Decimal(item.quantity) * self.DEFAULT_ITEM_WEIGHT_KG

        origin_city, origin_province = self.get_store_origin(store)
        return ShippingContext(
            store=store,
            province=province,
            city=city,
            subtotal=subtotal,
            weight_kg=weight_kg,
            item_count=item_count,
            origin_city=origin_city,
            origin_province=origin_province,
        )

    def get_quotes(self, store, province: str, city: str, cart=None, request=None) -> list[ShippingQuote]:
        context = self.build_context(store, province, city, cart, request)
        quotes = []
        methods = ShippingMethod.objects.filter(store=store, is_active=True).select_related("zone").order_by("sort_order")

        store_threshold = self._store_free_threshold(store)
        if store_threshold and context.subtotal >= store_threshold:
            quotes.append(
                ShippingQuote(
                    method_id=0,
                    slug="free-store",
                    name="ارسال رایگان",
                    provider="free",
                    calculation_mode="fixed",
                    price=Decimal("0"),
                    estimated_days=3,
                    is_free=True,
                )
            )

        for method in methods:
            provider = get_provider(method.provider)
            if not provider or not provider.is_available(method, context):
                continue
            price = provider.calculate(method, context)
            quotes.append(
                ShippingQuote(
                    method_id=method.id,
                    slug=method.slug,
                    name=method.name,
                    provider=method.provider,
                    calculation_mode=method.calculation_mode,
                    price=price,
                    estimated_days=method.estimated_days,
                    is_free=price == 0,
                )
            )
        return quotes

    def serialize_quote(self, quote: ShippingQuote) -> dict:
        return {
            "method_id": quote.method_id,
            "slug": quote.slug,
            "name": quote.name,
            "provider": quote.provider,
            "calculation_mode": quote.calculation_mode,
            "price": str(quote.price),
            "estimated_days": quote.estimated_days,
            "is_free": quote.is_free,
        }

    def list_methods(self, store):
        return [
            {
                "id": m.id,
                "name": m.name,
                "slug": m.slug,
                "provider": m.provider,
                "calculation_mode": m.calculation_mode,
                "estimated_days": m.estimated_days,
            }
            for m in ShippingMethod.objects.filter(store=store, is_active=True).order_by("sort_order")
        ]

    def _store_free_threshold(self, store) -> Decimal | None:
        from dashboard.services.store_admin import StoreAdminService

        settings = StoreAdminService()._get_group_settings(store, "shipping")
        threshold = settings.get("free_shipping_threshold")
        origin = settings.get("origin", {})
        if threshold is None and isinstance(origin, dict):
            threshold = origin.get("free_shipping_threshold")
        return Decimal(str(threshold)) if threshold else None
