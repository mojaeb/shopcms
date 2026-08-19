"""Concrete shipping providers."""

from decimal import Decimal

from shipping.engine import ShippingCalculator
from shipping.providers.base import ShippingContext, ShippingProvider
from shipping.providers.registry import register


class BaseCarrierProvider(ShippingProvider):
    calculator = ShippingCalculator()

    def calculate(self, method, context: ShippingContext) -> Decimal:
        threshold = method.free_shipping_threshold
        if threshold is not None and context.subtotal >= threshold:
            return Decimal("0")
        return self.calculator.calculate(method, context)


@register
class PostProvider(BaseCarrierProvider):
    codename = "post"
    label = "پست"

    def is_available(self, method, context: ShippingContext) -> bool:
        if not super().is_available(method, context):
            return False
        max_weight = method.config.get("max_weight_kg")
        if max_weight is not None and context.weight_kg > Decimal(str(max_weight)):
            return False
        return True


@register
class TipaxProvider(BaseCarrierProvider):
    codename = "tipax"
    label = "تیپاکس"


@register
class PeykProvider(BaseCarrierProvider):
    codename = "peyk"
    label = "پیک"

    def is_available(self, method, context: ShippingContext) -> bool:
        if not super().is_available(method, context):
            return False
        delivery_cities = method.config.get("delivery_cities") or []
        if delivery_cities and context.city not in delivery_cities:
            return False
        return True


@register
class FreeShippingProvider(ShippingProvider):
    codename = "free"
    label = "ارسال رایگان"

    def calculate(self, method, context: ShippingContext) -> Decimal:
        threshold = method.free_shipping_threshold or Decimal("0")
        if context.subtotal >= threshold:
            return Decimal("0")
        return Decimal(str(method.config.get("fallback_price", 0)))

    def is_available(self, method, context: ShippingContext) -> bool:
        threshold = method.free_shipping_threshold or Decimal("0")
        return context.subtotal >= threshold


@register
class ApiShippingProvider(BaseCarrierProvider):
    codename = "api"
    label = "API"

    def calculate(self, method, context: ShippingContext) -> Decimal:
        api_price = method.config.get("api_price")
        if api_price is not None:
            return Decimal(str(api_price))
        return super().calculate(method, context)
