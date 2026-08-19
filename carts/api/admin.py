"""Store admin discount API."""

from django.db import IntegrityError
from django.utils.dateparse import parse_datetime
from django.utils.timezone import get_current_timezone, is_naive, make_aware
from ninja import Router, Schema
from ninja.errors import HttpError

from carts.enums import DiscountScope, DiscountType
from carts.models import Coupon, GiftCard
from carts.services.discount import DiscountService
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


def _parse_optional_dt(value):
    if value in (None, ""):
        return None
    text = str(value).strip().replace("Z", "+00:00")
    dt = parse_datetime(text)
    if dt is None:
        raise HttpError(400, "تاریخ نامعتبر است")
    if is_naive(dt):
        dt = make_aware(dt, get_current_timezone())
    return dt


def _coupon_fields(data: dict, *, partial: bool) -> tuple[dict, dict]:
    m2m = {}
    for key in ("category_ids", "product_ids", "allowed_user_ids"):
        if key in data and data[key] is not None:
            m2m[key] = data.pop(key)
        elif key in data:
            data.pop(key)

    if "code" in data and data["code"] is not None:
        data["code"] = str(data["code"]).strip().upper()
        if not data["code"]:
            raise HttpError(400, "کد تخفیف الزامی است")

    for key in ("valid_from", "valid_until"):
        if key not in data:
            continue
        if data[key] in (None, "") and partial:
            data[key] = None
        else:
            data[key] = _parse_optional_dt(data[key])

    return data, m2m


@router.get("/coupons")
def list_coupons(request):
    store = _store(request)
    coupons = Coupon.objects.filter(store=store).prefetch_related("categories", "products", "allowed_users")
    return [service.serialize_coupon(c) for c in coupons]


@router.post("/coupons")
def create_coupon(request, payload: CouponCreateSchema):
    store = _store(request)
    data = payload.dict()
    data, m2m = _coupon_fields(data, partial=False)
    service.sync_plugin(store)
    try:
        coupon = Coupon.objects.create(store=store, **data)
    except IntegrityError as exc:
        raise HttpError(400, "این کد تخفیف قبلاً ثبت شده است") from exc
    if m2m.get("category_ids"):
        coupon.categories.set(m2m["category_ids"])
    if m2m.get("product_ids"):
        coupon.products.set(m2m["product_ids"])
    if m2m.get("allowed_user_ids"):
        coupon.allowed_users.set(m2m["allowed_user_ids"])
    return service.serialize_coupon(coupon)


@router.put("/coupons/{coupon_id}")
def update_coupon(request, coupon_id: int, payload: CouponUpdateSchema):
    store = _store(request)
    try:
        coupon = Coupon.objects.get(pk=coupon_id, store=store)
    except Coupon.DoesNotExist:
        raise HttpError(404, "کوپن یافت نشد")

    data = payload.dict(exclude_unset=True)
    data, m2m = _coupon_fields(data, partial=True)

    for field, value in data.items():
        setattr(coupon, field, value)
    try:
        coupon.save()
    except IntegrityError as exc:
        raise HttpError(400, "این کد تخفیف قبلاً ثبت شده است") from exc

    if "category_ids" in m2m:
        coupon.categories.set(m2m["category_ids"])
    if "product_ids" in m2m:
        coupon.products.set(m2m["product_ids"])
    if "allowed_user_ids" in m2m:
        coupon.allowed_users.set(m2m["allowed_user_ids"])

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
    service.sync_plugin(store)
    try:
        gift = GiftCard.objects.create(
            store=store,
            code=payload.code.strip().upper(),
            initial_balance=payload.initial_balance,
            balance=payload.initial_balance,
            owner_id=payload.owner_id,
            valid_until=_parse_optional_dt(payload.valid_until),
            is_active=payload.is_active,
        )
    except IntegrityError as exc:
        raise HttpError(400, "این کد کارت هدیه قبلاً ثبت شده است") from exc
    return service.serialize_gift_card(gift)


@router.put("/gift-cards/{gift_id}")
def update_gift_card(request, gift_id: int, payload: GiftCardUpdateSchema):
    store = _store(request)
    try:
        gift = GiftCard.objects.get(pk=gift_id, store=store)
    except GiftCard.DoesNotExist:
        raise HttpError(404, "کارت هدیه یافت نشد")

    data = payload.dict(exclude_unset=True)
    if "valid_until" in data:
        data["valid_until"] = _parse_optional_dt(data["valid_until"])
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
