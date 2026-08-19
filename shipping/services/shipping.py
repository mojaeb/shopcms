"""Shipping service layer."""

from decimal import Decimal

from carts.services.cart import CartService
from core.utils.geo import is_iran_coordinate
from shipping.distance import real_distance_km
from shipping.enums import ShippingPaymentType
from shipping.models import ShippingMethod
from shipping.providers.base import ShippingContext, ShippingQuote
from shipping.providers.registry import get_provider

_POSTPAID_SUFFIX = " - پس‌کرایه"


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

    def build_context(
        self,
        store,
        province: str,
        city: str,
        cart=None,
        request=None,
        dest_lat: float | None = None,
        dest_lng: float | None = None,
    ) -> ShippingContext:
        if cart is None and request is not None:
            cart = CartService().get_or_create_cart(store, request)
        subtotal = Decimal("0")
        item_count = 0
        weight_kg = Decimal("0")
        if cart:
            totals = CartService().calculate_totals(cart)
            subtotal = totals["subtotal"]
            for item in cart.items.select_related("product", "variant"):
                item_count += item.quantity
                weight_kg += Decimal(item.quantity) * self._item_weight_kg(item)
            weight_kg += self._package_weight_kg(store)

        origin_city, origin_province = self.get_store_origin(store)
        distance_km = self._calc_distance(store, dest_lat, dest_lng)
        return ShippingContext(
            store=store,
            province=province,
            city=city,
            subtotal=subtotal,
            weight_kg=weight_kg,
            item_count=item_count,
            origin_city=origin_city,
            origin_province=origin_province,
            distance_km=distance_km,
        )

    def _calc_distance(self, store, dest_lat: float | None, dest_lng: float | None) -> Decimal | None:
        """Compute distance_km when both store origin and destination coordinates are available."""
        origin_lat = getattr(store, "origin_latitude", None)
        origin_lng = getattr(store, "origin_longitude", None)
        if origin_lat is None or origin_lng is None or dest_lat is None or dest_lng is None:
            return None
        if not is_iran_coordinate(float(dest_lat), float(dest_lng)):
            return None
        api_key = self._routing_api_key(store)
        return real_distance_km(
            float(origin_lat), float(origin_lng),
            float(dest_lat), float(dest_lng),
            api_key=api_key,
            store_id=store.pk,
        )

    def _routing_api_key(self, store) -> str:
        from dashboard.services.store_admin import StoreAdminService

        settings = StoreAdminService()._get_group_settings(store, "shipping")
        return settings.get("map", {}).get("routing_api_key", "") or ""

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
                    payment_type=ShippingPaymentType.PREPAID,
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
                    name=self._quote_name(method),
                    provider=method.provider,
                    calculation_mode=method.calculation_mode,
                    price=price,
                    estimated_days=method.estimated_days,
                    is_free=price == 0,
                    payment_type=method.payment_type or ShippingPaymentType.PREPAID,
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
            "payment_type": quote.payment_type,
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

    def _item_weight_kg(self, item) -> Decimal:
        variant = getattr(item, "variant", None)
        if variant is not None and variant.weight_kg is not None:
            return Decimal(str(variant.weight_kg))
        product = item.product
        if product is not None and product.weight_kg is not None:
            return Decimal(str(product.weight_kg))
        return self.DEFAULT_ITEM_WEIGHT_KG

    def _package_weight_kg(self, store) -> Decimal:
        from dashboard.services.store_admin import StoreAdminService

        settings = StoreAdminService()._get_group_settings(store, "shipping")
        raw = settings.get("base_package_weight_kg")
        if raw is None and isinstance(settings.get("origin"), dict):
            raw = settings["origin"].get("base_package_weight_kg")
        if raw is None:
            return Decimal("0")
        return Decimal(str(raw))

    def _quote_name(self, method: ShippingMethod) -> str:
        name = method.name
        if method.payment_type == ShippingPaymentType.POSTPAID and "پس‌کرایه" not in name:
            return f"{name}{_POSTPAID_SUFFIX}"
        return name

    def _store_free_threshold(self, store) -> Decimal | None:
        from dashboard.services.store_admin import StoreAdminService

        settings = StoreAdminService()._get_group_settings(store, "shipping")
        threshold = settings.get("free_shipping_threshold")
        origin = settings.get("origin", {})
        if threshold is None and isinstance(origin, dict):
            threshold = origin.get("free_shipping_threshold")
        return Decimal(str(threshold)) if threshold else None
