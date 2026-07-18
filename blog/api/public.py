"""Public blog API."""

from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination, paginate

from accounts.models import User
from accounts.services.jwt import JWTService
from blog.services.blog import BlogError, BlogService
from tenants.context import get_current_store

router = Router()
service = BlogService()


class BlogCommentCreateSchema(Schema):
    body: str
    parent_id: int | None = None


class PostListSchema(Schema):
    id: int
    title: str
    slug: str
    excerpt: str
    featured_image: str
    category: str | None = None
    category_slug: str | None = None
    tags: list
    author: str
    published_at: str | None = None


class PostDetailSchema(PostListSchema):
    content: str
    seo: dict


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


@router.get("/posts", response=list[PostListSchema])
@paginate(PageNumberPagination, page_size=12)
def list_posts(request, category: str | None = None, tag: str | None = None):
    store = _store(request)
    if not service.is_active(store):
        return []
    qs = service.list_published_posts(store, category, tag)
    return [service.serialize_post_list(p) for p in qs]


@router.get("/posts/{slug}", response=PostDetailSchema)
def get_post(request, slug: str):
    store = _store(request)
    try:
        post = service.get_post(store, slug)
        return service.serialize_post_detail(post)
    except BlogError as e:
        raise HttpError(404, str(e))


@router.get("/categories")
def list_categories(request):
    store = _store(request)
    return [service.serialize_category(c) for c in service.list_categories(store)]


@router.get("/tags")
def list_tags(request):
    store = _store(request)
    return [service.serialize_tag(t) for t in service.list_tags(store)]


@router.get("/posts/{slug}/comments")
def list_comments(request, slug: str):
    store = _store(request)
    try:
        comments = service.list_post_comments(store, slug)
        return [service.serialize_comment(c) for c in comments]
    except BlogError as e:
        raise HttpError(404, str(e))


@router.post("/posts/{slug}/comments")
def create_comment(request, slug: str, payload: BlogCommentCreateSchema):
    store = _store(request)
    user = _user(request)
    try:
        comment = service.create_comment(user, store, slug, payload.body, payload.parent_id)
        return service.serialize_comment(comment, include_replies=False)
    except BlogError as e:
        raise HttpError(400, str(e))
