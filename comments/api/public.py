"""Public comment API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.models import User
from accounts.services.jwt import JWTService
from comments.services.comment import CommentError, CommentService
from tenants.context import get_current_store

router = Router()
service = CommentService()


class CommentCreateSchema(Schema):
    product_slug: str
    body: str
    rating: int | None = None
    parent_id: int | None = None


class CommentLikeSchema(Schema):
    comment_id: int


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


def _optional_user(request):
    try:
        return _user(request)
    except HttpError:
        return None


@router.get("/product/{product_slug}")
def list_product_comments(request, product_slug: str):
    store = _store(request)
    if not service.is_active(store):
        return {"summary": {"average_rating": 0, "review_count": 0}, "items": []}
    user = _optional_user(request)
    comments = service.list_product_comments(store, product_slug, user)
    summary = service.get_product_summary(store, product_slug)
    return {
        "summary": summary,
        "items": [service.serialize_comment(c, user) for c in comments],
    }


@router.get("/mine")
def list_my_comments(request):
    store = _store(request)
    user = _user(request)
    comments = service.list_user_comments(user, store)
    return [service.serialize_comment(c, user, include_replies=False) for c in comments]


@router.post("/")
def create_comment(request, payload: CommentCreateSchema):
    store = _store(request)
    user = _user(request)
    try:
        comment = service.create_comment(
            user, store, payload.product_slug, payload.body, payload.rating, payload.parent_id,
        )
        return service.serialize_comment(comment, user, include_replies=False)
    except CommentError as e:
        raise HttpError(400, str(e))


@router.post("/like")
def toggle_like(request, payload: CommentLikeSchema):
    store = _store(request)
    user = _user(request)
    try:
        return service.toggle_like(user, store, payload.comment_id)
    except CommentError as e:
        raise HttpError(400, str(e))
