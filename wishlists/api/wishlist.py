"""Wishlist API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.models import User
from accounts.services.jwt import JWTService
from tenants.context import get_current_store
from wishlists.services.wishlist import WishlistError, WishlistService

router = Router()
service = WishlistService()


class WishlistProductSchema(Schema):
    product_slug: str


class WishlistRemoveSchema(Schema):
    product_id: int | None = None
    product_slug: str | None = None


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


def _user(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Bearer "):
        payload = JWTService().verify_access_token(auth_header[7:])
        if payload:
            user = User.objects.filter(pk=int(payload["sub"]), is_active=True).first()
            if user:
                return user
    if getattr(request, "user", None) and request.user.is_authenticated:
        return request.user
    raise HttpError(401, "ورود الزامی است")


@router.get("/")
def list_wishlist(request):
    store = _store(request)
    user = _user(request)
    if not service.is_active(store):
        return []
    items = service.list_items(user, store)
    return [service.serialize_item(item) for item in items]


@router.get("/count")
def wishlist_count(request):
    store = _store(request)
    try:
        user = _user(request)
    except HttpError:
        return {"count": 0, "enabled": service.is_active(store)}
    return {"count": service.get_count(user, store), "enabled": service.is_active(store)}


@router.get("/check/{product_slug}")
def check_wishlist(request, product_slug: str):
    store = _store(request)
    if not service.is_active(store):
        return {"in_wishlist": False, "enabled": False}
    try:
        user = _user(request)
        return {"in_wishlist": service.is_in_wishlist(user, store, product_slug), "enabled": True}
    except HttpError:
        return {"in_wishlist": False, "enabled": True}


@router.post("/add")
def add_to_wishlist(request, payload: WishlistProductSchema):
    store = _store(request)
    user = _user(request)
    try:
        service.add_item(user, store, payload.product_slug)
        return {"success": True, "count": service.get_count(user, store)}
    except WishlistError as e:
        raise HttpError(400, str(e))


@router.post("/remove")
def remove_from_wishlist(request, payload: WishlistRemoveSchema):
    store = _store(request)
    user = _user(request)
    try:
        service.remove_item(user, store, payload.product_id, payload.product_slug)
        return {"success": True, "count": service.get_count(user, store)}
    except WishlistError as e:
        raise HttpError(400, str(e))


@router.post("/toggle")
def toggle_wishlist(request, payload: WishlistProductSchema):
    store = _store(request)
    user = _user(request)
    try:
        result = service.toggle_item(user, store, payload.product_slug)
        result["count"] = service.get_count(user, store)
        return result
    except WishlistError as e:
        raise HttpError(400, str(e))
