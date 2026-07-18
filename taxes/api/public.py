"""Public tax API."""

from decimal import Decimal

from ninja import Router, Schema
from ninja.errors import HttpError

from carts.services.cart import CartService
from taxes.services.tax import TaxService
from tenants.context import get_current_store

router = Router()
service = TaxService()
cart_service = CartService()


class TaxPreviewSchema(Schema):
    shipping_price: float = 0


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/settings")
def tax_settings(request):
    store = _store(request)
    return service.get_tax_settings(store)


@router.post("/preview")
def tax_preview(request, payload: TaxPreviewSchema):
    store = _store(request)
    cart = cart_service.get_or_create_cart(store, request)
    result = service.calculate_for_cart(store, cart, Decimal(str(payload.shipping_price)))
    totals = cart_service.calculate_totals(cart)
    cart_total = totals["total"] + Decimal(str(payload.shipping_price))
    result["cart_total"] = str(int(cart_total))
    result["payable_total"] = str(int(cart_total + Decimal(result["tax"])))
    return result
