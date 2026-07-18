"""Store admin comment moderation API."""

from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination, paginate

from dashboard.authentication_store import store_comments_auth
from comments.services.comment import CommentError, CommentService
from tenants.context import get_current_store

router = Router(auth=store_comments_auth)
service = CommentService()


class CommentModerateSchema(Schema):
    status: str


class CommentAdminSchema(Schema):
    id: int
    product_id: int
    product_name: str
    product_slug: str
    user: dict
    rating: int | None
    body: str
    status: str
    status_label: str
    likes_count: int
    is_verified_purchase: bool
    created_at: str
    replies: list = []


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/", response=list[CommentAdminSchema])
@paginate(PageNumberPagination, page_size=20)
def list_comments(request, status: str | None = None):
    store = _store(request)
    qs = service.list_store_comments(store, status=status)
    return [service.serialize_comment(c, include_replies=True) for c in qs]


@router.get("/stats")
def comment_stats(request):
    store = _store(request)
    return {
        "pending": service.get_pending_count(store),
        "total": service.list_store_comments(store).count(),
    }


@router.put("/{comment_id}/status")
def moderate_comment(request, comment_id: int, payload: CommentModerateSchema):
    store = _store(request)
    try:
        comment = service.moderate_comment(store, comment_id, payload.status)
        return service.serialize_comment(comment, include_replies=False)
    except CommentError as e:
        raise HttpError(400, str(e))
