"""Shipping price calculators."""

from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q

from shipping.data.province_adjacency import zone_tier
from shipping.enums import CalculationMode
from shipping.models import ShippingMethod, ShippingPrice


class ShippingCalculator:
    """Shared calculation logic for all providers."""

    def calculate(self, method: ShippingMethod, context) -> Decimal:
        mode = method.calculation_mode
        if mode == CalculationMode.FIXED:
            price = self._fixed(method)
        elif mode == CalculationMode.DISTANCE:
            price = self._distance(method, context)
        elif mode == CalculationMode.WEIGHT:
            price = self._weight(method, context)
        elif mode == CalculationMode.DISTANCE_WEIGHT:
            price = self._distance_weight(method, context)
        elif mode == CalculationMode.API:
            price = Decimal(str(method.config.get("fallback_price", 0)))
        else:
            price = Decimal("0")
        return self._apply_extra_cost(method, price)

    def _fixed(self, method: ShippingMethod) -> Decimal:
        return Decimal(str(method.config.get("fixed_price", 0)))

    def _distance(self, method: ShippingMethod, context) -> Decimal:
        row = self._find_price_row(method, context, use_weight=False)
        return row.price if row else Decimal(str(method.config.get("fixed_price", 0)))

    def _weight(self, method: ShippingMethod, context) -> Decimal:
        row = self._find_price_row(method, context, use_weight=True)
        return row.price if row else Decimal(str(method.config.get("fixed_price", 0)))

    def _distance_weight(self, method: ShippingMethod, context) -> Decimal:
        row = self._find_price_row(method, context, use_weight=True)
        if not row:
            return Decimal(str(method.config.get("fixed_price", 0)))
        base_weight = Decimal(str(method.config.get("base_weight_kg", 1)))
        extra = max(Decimal("0"), context.weight_kg - base_weight)
        return row.price + (extra * row.extra_per_kg)

    def _apply_extra_cost(self, method: ShippingMethod, price: Decimal) -> Decimal:
        extra_flat = Decimal(str(method.config.get("extra_cost_flat", 0)))
        extra_percent = Decimal(str(method.config.get("extra_cost_percent", 0)))
        total = price + extra_flat + (price * extra_percent / Decimal("100"))
        return total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    def _find_price_row(self, method: ShippingMethod, context, use_weight: bool):
        qs = ShippingPrice.objects.filter(method=method)
        city_rows = qs.filter(zone_tier="")
        row = self._match_price_rows(city_rows, method, context, use_weight)
        if row:
            return row

        tier = zone_tier(context.origin_province, context.province)
        origin = context.origin_city or method.config.get("origin_city", "")
        tier_rows = qs.filter(zone_tier=tier, to_city="")
        if origin:
            tier_rows = tier_rows.filter(Q(from_city="") | Q(from_city=origin))
        return self._match_price_rows(tier_rows, method, context, use_weight, city_required=False)

    def _match_price_rows(self, qs, method: ShippingMethod, context, use_weight: bool, city_required: bool = True):
        if use_weight:
            for row in qs.order_by("weight_min_kg"):
                if city_required and row.to_city and context.city and row.to_city != context.city:
                    continue
                max_w = row.weight_max_kg
                if context.weight_kg >= row.weight_min_kg and (max_w is None or context.weight_kg <= max_w):
                    return row
            return None

        origin = context.origin_city or method.config.get("origin_city", "")
        filtered = qs
        if city_required:
            if origin:
                filtered = filtered.filter(from_city=origin)
            if context.city:
                filtered = filtered.filter(to_city=context.city)
        return filtered.order_by("price").first()
