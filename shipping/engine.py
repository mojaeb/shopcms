"""Shipping price calculators."""

from decimal import Decimal

from shipping.enums import CalculationMode
from shipping.models import ShippingMethod, ShippingPrice


class ShippingCalculator:
    """Shared calculation logic for all providers."""

    def calculate(self, method: ShippingMethod, context) -> Decimal:
        mode = method.calculation_mode
        if mode == CalculationMode.FIXED:
            return self._fixed(method)
        if mode == CalculationMode.DISTANCE:
            return self._distance(method, context)
        if mode == CalculationMode.WEIGHT:
            return self._weight(method, context)
        if mode == CalculationMode.DISTANCE_WEIGHT:
            return self._distance_weight(method, context)
        if mode == CalculationMode.API:
            return Decimal(str(method.config.get("fallback_price", 0)))
        return Decimal("0")

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

    def _find_price_row(self, method: ShippingMethod, context, use_weight: bool):
        qs = ShippingPrice.objects.filter(method=method)

        if use_weight:
            for row in qs.order_by("weight_min_kg"):
                if row.to_city and context.city and row.to_city != context.city:
                    continue
                max_w = row.weight_max_kg
                if context.weight_kg >= row.weight_min_kg and (max_w is None or context.weight_kg <= max_w):
                    return row
            return None

        origin = context.origin_city or method.config.get("origin_city", "")
        if origin:
            qs = qs.filter(from_city=origin)
        if context.city:
            qs = qs.filter(to_city=context.city)
        return qs.order_by("price").first()
