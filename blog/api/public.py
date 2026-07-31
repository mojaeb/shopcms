"""Public blog API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.models import User
from accounts.services.jwt import JWTService
from blog.services.blog import BlogError, BlogService
from core.cache import cache_manager
from core.cache.keys import blog_detail, blog_list
from tenants.context import get_current_store

router = Router()
service = BlogService()

BLOG_PAGE_SIZE = 12
BLOG_MAX_PAGE_SIZE = 50


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


def _clamp_page(page: int, page_size: int) -> tuple[int, int]:
    page = max(1, page or 1)
    page_size = min(max(page_size or BLOG_PAGE_SIZE, 1), BLOG_MAX_PAGE_SIZE)
    return page, page_size


@router.get("/posts")
def list_posts(
    request,
    category: str | None = None,
    tag: str | None = None,
    page: int = 1,
    page_size: int = BLOG_PAGE_SIZE,
):
    store = _store(request)
    if not service.is_active(store):
        return {"items": [], "count": 0}

    page, page_size = _clamp_page(page, page_size)
    params = {"category": category, "tag": tag, "page": page, "page_size": page_size}
    cache_key = blog_list(store.id, cache_manager.hash_params(params))

    def factory():
        qs = service.list_published_posts(store, category, tag)
        count = qs.count()
        offset = (page - 1) * page_size
        items = [service.serialize_post_list(p) for p in qs[offset : offset + page_size]]
        return {"items": items, "count": count}

    return cache_manager.get_or_set(cache_key, factory, ttl="medium")


@router.get("/posts/{slug}", response=PostDetailSchema)
def get_post(request, slug: str):
    store = _store(request)
    cache_key = blog_detail(store.id, slug)
    cached = cache_manager.get(cache_key)
    if cached is not None:
        if cached == "__missing__":
            raise HttpError(404, "مقاله یافت نشد")
        return cached

    try:
        post = service.get_post(store, slug)
        payload = service.serialize_post_detail(post)
        cache_manager.set(cache_key, payload, ttl="medium")
        return payload
    except BlogError as e:
        cache_manager.set(cache_key, "__missing__", ttl="short")
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
