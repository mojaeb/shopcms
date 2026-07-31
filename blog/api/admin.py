"""Store admin blog API."""

from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination, paginate

from blog.models import BlogPost
from blog.services.blog import BlogError, BlogService
from dashboard.authentication_store import store_content_auth
from tenants.context import get_current_store

router = Router(auth=store_content_auth)
service = BlogService()


class PostCreateSchema(Schema):
    title: str
    slug: str
    excerpt: str = ""
    content: str = ""
    featured_image: str = ""
    category_id: int | None = None
    tag_ids: list[int] = []
    is_published: bool = False
    meta_title: str = ""
    meta_description: str = ""
    meta_keywords: str = ""
    og_image: str = ""
    canonical_url: str = ""
    robots: str = "index,follow"


class PostUpdateSchema(Schema):
    title: str | None = None
    slug: str | None = None
    excerpt: str | None = None
    content: str | None = None
    featured_image: str | None = None
    category_id: int | None = None
    tag_ids: list[int] | None = None
    is_published: bool | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    og_image: str | None = None
    canonical_url: str | None = None
    robots: str | None = None


class CategoryCreateSchema(Schema):
    name: str
    slug: str
    description: str = ""


class TagCreateSchema(Schema):
    name: str
    slug: str


class CommentModerateSchema(Schema):
    status: str


class PostAdminSchema(Schema):
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
    is_published: bool


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/posts", response=list[PostAdminSchema])
@paginate(PageNumberPagination, page_size=20)
def list_posts(request):
    store = _store(request)
    posts = service.list_all_posts(store)
    return [
        {**service.serialize_post_list(p), "is_published": p.is_published}
        for p in posts
    ]


@router.get("/posts/{post_id}")
def get_post(request, post_id: int):
    store = _store(request)
    try:
        post = BlogPost.objects.select_related("category", "author").prefetch_related("tags").get(
            pk=post_id, store=store
        )
    except BlogPost.DoesNotExist:
        raise HttpError(404, "مقاله یافت نشد")
    return service.serialize_post_detail(post, render_content=False)


@router.post("/posts")
def create_post(request, payload: PostCreateSchema):
    store = _store(request)
    user = getattr(request, "auth", None)
    data = payload.dict()
    tag_ids = data.pop("tag_ids", [])
    try:
        post = service.create_post(store, user, {**data, "tag_ids": tag_ids})
        return service.serialize_post_detail(post, render_content=False)
    except BlogError as e:
        raise HttpError(400, str(e))


@router.put("/posts/{post_id}")
def update_post(request, post_id: int, payload: PostUpdateSchema):
    store = _store(request)
    data = {k: v for k, v in payload.dict().items() if v is not None}
    try:
        post = service.update_post(store, post_id, data)
        return service.serialize_post_detail(post, render_content=False)
    except BlogError as e:
        raise HttpError(400, str(e))


@router.delete("/posts/{post_id}")
def delete_post(request, post_id: int):
    store = _store(request)
    try:
        service.delete_post(store, post_id)
        return {"success": True}
    except BlogError as e:
        raise HttpError(404, str(e))


@router.get("/categories")
def list_categories(request):
    store = _store(request)
    return [service.serialize_category(c) for c in service.list_categories(store, active_only=False)]


@router.post("/categories")
def create_category(request, payload: CategoryCreateSchema):
    store = _store(request)
    category = service.create_category(store, payload.dict())
    return service.serialize_category(category)


@router.get("/tags")
def list_tags(request):
    store = _store(request)
    return [service.serialize_tag(t) for t in service.list_tags(store)]


@router.post("/tags")
def create_tag(request, payload: TagCreateSchema):
    store = _store(request)
    tag = service.create_tag(store, payload.dict())
    return service.serialize_tag(tag)


@router.get("/comments/pending")
def pending_comments(request):
    store = _store(request)
    comments = service.list_pending_comments(store)
    return [
        {
            "id": c.id,
            "source": "blog",
            "post_title": c.post.title,
            "post_slug": c.post.slug,
            "parent_id": c.parent_id,
            "user": c.user.full_name or c.user.phone,
            "body": c.body,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
        }
        for c in comments
    ]


@router.get("/comments")
def list_comments(request, status: str | None = None):
    store = _store(request)
    comments = service.list_store_comments(store, status=status)
    return [
        {
            "id": c.id,
            "source": "blog",
            "post_title": c.post.title,
            "post_slug": c.post.slug,
            "parent_id": c.parent_id,
            "user": c.user.full_name or c.user.phone,
            "body": c.body,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
        }
        for c in comments
    ]


@router.put("/comments/{comment_id}/status")
def moderate_comment(request, comment_id: int, payload: CommentModerateSchema):
    store = _store(request)
    try:
        comment = service.moderate_comment(store, comment_id, payload.status)
        return service.serialize_comment(comment, include_replies=False)
    except BlogError as e:
        raise HttpError(400, str(e))
