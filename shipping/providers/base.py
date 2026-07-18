"""Shipping provider base classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from shipping.models import ShippingMethod


@dataclass
class ShippingContext:
    store: object
    province: str
    city: str
    subtotal: Decimal
    weight_kg: Decimal
    item_count: int
    origin_city: str = ""
    origin_province: str = ""


@dataclass
class ShippingQuote:
    method_id: int
    slug: str
    name: str
    provider: str
    calculation_mode: str
    price: Decimal
    estimated_days: int
    is_free: bool = False


class ShippingProvider(ABC):
    codename: str = ""
    label: str = ""

    @abstractmethod
    def calculate(self, method: ShippingMethod, context: ShippingContext) -> Decimal:
        pass

    def is_available(self, method: ShippingMethod, context: ShippingContext) -> bool:
        if method.min_order_amount and context.subtotal < method.min_order_amount:
            return False
        if method.zone_id and not method.zone.matches(context.province, context.city):
            return False
        return True
