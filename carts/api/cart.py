"""Cart API endpoints."""

from ninja import Router, Schema
from ninja.errors import HttpError

from carts.services.cart import CartError, CartService
from tenants.context import get_current_store

router = Router()
service = CartService()


class CartAddSchema(Schema):
    product_slug: str
    variant_id: int | None = None
    quantity: int = 1


class CartUpdateSchema(Schema):
    item_id: int
    quantity: int


class CartRemoveSchema(Schema):
    item_id: int


class CartCouponSchema(Schema):
    code: str


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


def _cart(request):
    return service.get_or_create_cart(_store(request), request)


def _require_user(request):
    user = service._resolve_user(request)
    if not user:
        raise HttpError(401, "ورود الزامی است")
    return user


@router.get("/")
def get_cart(request):
    cart = _cart(request)
    return service.serialize_cart(cart)


@router.get("/count")
def cart_count(request):
    cart = _cart(request)
    totals = service.calculate_totals(cart)
    return {"item_count": totals["item_count"], "total": str(totals["total"])}


@router.post("/add")
def add_to_cart(request, payload: CartAddSchema):
    _require_user(request)
    try:
        item = service.add_item(_cart(request), payload.product_slug, payload.variant_id, payload.quantity)
        cart = item.cart
        return service.serialize_cart(cart)
    except CartError as e:
        raise HttpError(400, str(e))


@router.post("/update")
def update_cart(request, payload: CartUpdateSchema):
    try:
        cart = service.update_item(_cart(request), payload.item_id, payload.quantity)
        return service.serialize_cart(cart)
    except CartError as e:
        raise HttpError(400, str(e))


@router.post("/remove")
def remove_from_cart(request, payload: CartRemoveSchema):
    try:
        cart = service.remove_item(_cart(request), payload.item_id)
        return service.serialize_cart(cart)
    except CartError as e:
        raise HttpError(400, str(e))


@router.post("/coupon/apply")
def apply_coupon(request, payload: CartCouponSchema):
    try:
        cart = service.apply_coupon(_cart(request), payload.code)
        return service.serialize_cart(cart)
    except CartError as e:
        raise HttpError(400, str(e))


@router.post("/coupon/remove")
def remove_coupon(request):
    cart = service.remove_coupon(_cart(request))
    return service.serialize_cart(cart)


@router.post("/gift-card/apply")
def apply_gift_card(request, payload: CartCouponSchema):
    try:
        cart = service.apply_gift_card(_cart(request), payload.code)
        return service.serialize_cart(cart)
    except CartError as e:
        raise HttpError(400, str(e))


@router.post("/gift-card/remove")
def remove_gift_card(request):
    cart = service.remove_gift_card(_cart(request))
    return service.serialize_cart(cart)
