"""Store admin discount API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from carts.enums import DiscountScope, DiscountType
from carts.models import Coupon, GiftCard
from carts.services.discount import DiscountError, DiscountService
from dashboard.authentication_store import store_settings_auth
from tenants.context import get_current_store

router = Router(auth=store_settings_auth)
service = DiscountService()


class CouponCreateSchema(Schema):
    code: str
    discount_type: str = DiscountType.PERCENTAGE
    value: float
    scope: str = DiscountScope.ALL
    min_order_amount: float = 0
    max_uses: int | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    is_active: bool = True
    first_purchase_only: bool = False
    max_discount_amount: float | None = None
    per_user_limit: int | None = None
    category_ids: list[int] = []
    product_ids: list[int] = []
    allowed_user_ids: list[int] = []


class CouponUpdateSchema(Schema):
    code: str | None = None
    discount_type: str | None = None
    value: float | None = None
    scope: str | None = None
    min_order_amount: float | None = None
    max_uses: int | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    is_active: bool | None = None
    first_purchase_only: bool | None = None
    max_discount_amount: float | None = None
    per_user_limit: int | None = None
    category_ids: list[int] | None = None
    product_ids: list[int] | None = None
    allowed_user_ids: list[int] | None = None


class GiftCardCreateSchema(Schema):
    code: str
    initial_balance: float
    owner_id: int | None = None
    valid_until: str | None = None
    is_active: bool = True


class GiftCardUpdateSchema(Schema):
    balance: float | None = None
    owner_id: int | None = None
    valid_until: str | None = None
    is_active: bool | None = None


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/coupons")
def list_coupons(request):
    store = _store(request)
    coupons = Coupon.objects.filter(store=store).prefetch_related("categories", "products", "allowed_users")
    return [service.serialize_coupon(c) for c in coupons]


@router.post("/coupons")
def create_coupon(request, payload: CouponCreateSchema):
    store = _store(request)
    data = payload.dict()
    m2m = {
        "category_ids": data.pop("category_ids", []),
        "product_ids": data.pop("product_ids", []),
        "allowed_user_ids": data.pop("allowed_user_ids", []),
    }
    data["code"] = data["code"].strip().upper()
    coupon = Coupon.objects.create(store=store, **data)
    if m2m["category_ids"]:
        coupon.categories.set(m2m["category_ids"])
    if m2m["product_ids"]:
        coupon.products.set(m2m["product_ids"])
    if m2m["allowed_user_ids"]:
        coupon.allowed_users.set(m2m["allowed_user_ids"])
    return service.serialize_coupon(coupon)


@router.put("/coupons/{coupon_id}")
def update_coupon(request, coupon_id: int, payload: CouponUpdateSchema):
    store = _store(request)
    try:
        coupon = Coupon.objects.get(pk=coupon_id, store=store)
    except Coupon.DoesNotExist:
        raise HttpError(404, "کوپن یافت نشد")

    data = {k: v for k, v in payload.dict().items() if v is not None}
    m2m_fields = {}
    for key in ("category_ids", "product_ids", "allowed_user_ids"):
        if key in data:
            m2m_fields[key] = data.pop(key)

    if "code" in data:
        data["code"] = data["code"].strip().upper()

    for field, value in data.items():
        setattr(coupon, field, value)
    coupon.save()

    if "category_ids" in m2m_fields:
        coupon.categories.set(m2m_fields["category_ids"])
    if "product_ids" in m2m_fields:
        coupon.products.set(m2m_fields["product_ids"])
    if "allowed_user_ids" in m2m_fields:
        coupon.allowed_users.set(m2m_fields["allowed_user_ids"])

    return service.serialize_coupon(coupon)


@router.delete("/coupons/{coupon_id}")
def delete_coupon(request, coupon_id: int):
    store = _store(request)
    deleted, _ = Coupon.objects.filter(pk=coupon_id, store=store).delete()
    if not deleted:
        raise HttpError(404, "کوپن یافت نشد")
    return {"success": True}


@router.get("/gift-cards")
def list_gift_cards(request):
    store = _store(request)
    return [service.serialize_gift_card(g) for g in GiftCard.objects.filter(store=store)]


@router.post("/gift-cards")
def create_gift_card(request, payload: GiftCardCreateSchema):
    store = _store(request)
    gift = GiftCard.objects.create(
        store=store,
        code=payload.code.strip().upper(),
        initial_balance=payload.initial_balance,
        balance=payload.initial_balance,
        owner_id=payload.owner_id,
        valid_until=payload.valid_until,
        is_active=payload.is_active,
    )
    return service.serialize_gift_card(gift)


@router.put("/gift-cards/{gift_id}")
def update_gift_card(request, gift_id: int, payload: GiftCardUpdateSchema):
    store = _store(request)
    try:
        gift = GiftCard.objects.get(pk=gift_id, store=store)
    except GiftCard.DoesNotExist:
        raise HttpError(404, "کارت هدیه یافت نشد")

    data = {k: v for k, v in payload.dict().items() if v is not None}
    for field, value in data.items():
        setattr(gift, field, value)
    gift.save()
    return service.serialize_gift_card(gift)


@router.delete("/gift-cards/{gift_id}")
def delete_gift_card(request, gift_id: int):
    store = _store(request)
    deleted, _ = GiftCard.objects.filter(pk=gift_id, store=store).delete()
    if not deleted:
        raise HttpError(404, "کارت هدیه یافت نشد")
    return {"success": True}
