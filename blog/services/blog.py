"""Blog service layer."""

import logging

from django.db import transaction
from django.utils import timezone

from blog.models import BlogCategory, BlogComment, BlogPost, BlogTag
from cms.services.cms import CMSService
from comments.enums import CommentStatus
from tenants.models import StorePlugin

logger = logging.getLogger(__name__)


class BlogError(Exception):
    pass


class BlogService:
    """Blog posts, categories, tags, and comments."""

    def __init__(self):
        self.cms = CMSService()

    def is_active(self, store) -> bool:
        from plugins.services.plugin import PluginService

        return PluginService().is_enabled(store, "blog")

    def list_published_posts(self, store, category_slug: str | None = None, tag_slug: str | None = None):
        qs = BlogPost.objects.filter(store=store, is_published=True).select_related("category", "author").prefetch_related("tags")
        if category_slug:
            qs = qs.filter(category__slug=category_slug, category__is_active=True)
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)
        return qs.order_by("-published_at", "-created_at")

    def list_all_posts(self, store):
        return BlogPost.objects.filter(store=store).select_related("category", "author").prefetch_related("tags")

    def get_post(self, store, slug: str, published_only: bool = True) -> BlogPost:
        qs = BlogPost.objects.filter(store=store, slug=slug).select_related("category", "author").prefetch_related("tags")
        if published_only:
            qs = qs.filter(is_published=True)
        post = qs.first()
        if not post:
            raise BlogError("مقاله یافت نشد")
        return post

    def list_categories(self, store, active_only: bool = True):
        qs = BlogCategory.objects.filter(store=store)
        if active_only:
            qs = qs.filter(is_active=True)
        return qs.order_by("name")

    def list_tags(self, store):
        return BlogTag.objects.filter(store=store).order_by("name")

    @transaction.atomic
    def create_post(self, store, author, data: dict) -> BlogPost:
        if not self.is_active(store):
            raise BlogError("وبلاگ برای این فروشگاه فعال نیست")
        tags = data.pop("tag_ids", [])
        post = BlogPost.objects.create(store=store, author=author, **data)
        if tags:
            post.tags.set(BlogTag.objects.filter(store=store, pk__in=tags))
        return post

    @transaction.atomic
    def update_post(self, store, post_id: int, data: dict) -> BlogPost:
        try:
            post = BlogPost.objects.get(pk=post_id, store=store)
        except BlogPost.DoesNotExist:
            raise BlogError("مقاله یافت نشد")
        tag_ids = data.pop("tag_ids", None)
        for field, value in data.items():
            setattr(post, field, value)
        post.save()
        if tag_ids is not None:
            post.tags.set(BlogTag.objects.filter(store=store, pk__in=tag_ids))
        return post

    @transaction.atomic
    def delete_post(self, store, post_id: int) -> None:
        deleted, _ = BlogPost.objects.filter(pk=post_id, store=store).delete()
        if not deleted:
            raise BlogError("مقاله یافت نشد")

    @transaction.atomic
    def create_category(self, store, data: dict) -> BlogCategory:
        return BlogCategory.objects.create(store=store, **data)

    @transaction.atomic
    def create_tag(self, store, data: dict) -> BlogTag:
        return BlogTag.objects.create(store=store, **data)

    def list_post_comments(self, store, post_slug: str):
        post = self.get_post(store, post_slug)
        return (
            BlogComment.objects.filter(store=store, post=post, parent__isnull=True, status=CommentStatus.APPROVED)
            .select_related("user")
            .prefetch_related("replies__user")
        )

    @transaction.atomic
    def create_comment(self, user, store, post_slug: str, body: str, parent_id: int | None = None) -> BlogComment:
        if not self.is_active(store):
            raise BlogError("وبلاگ فعال نیست")
        body = body.strip()
        if len(body) < 3:
            raise BlogError("متن نظر خیلی کوتاه است")
        post = self.get_post(store, post_slug)
        parent = None
        if parent_id:
            parent = BlogComment.objects.filter(pk=parent_id, store=store, post=post).first()
            if not parent:
                raise BlogError("نظر والد یافت نشد")
        return BlogComment.objects.create(store=store, post=post, user=user, parent=parent, body=body)

    @transaction.atomic
    def moderate_comment(self, store, comment_id: int, status: str) -> BlogComment:
        if status not in CommentStatus.values:
            raise BlogError("وضعیت نامعتبر است")
        try:
            comment = BlogComment.objects.get(pk=comment_id, store=store)
        except BlogComment.DoesNotExist:
            raise BlogError("نظر یافت نشد")
        comment.status = status
        comment.save(update_fields=["status", "updated_at"])
        return comment

    def list_pending_comments(self, store):
        return BlogComment.objects.filter(store=store, status=CommentStatus.PENDING).select_related("post", "user")

    def serialize_post_list(self, post: BlogPost) -> dict:
        return {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "excerpt": post.excerpt,
            "featured_image": post.featured_image,
            "category": post.category.name if post.category_id else None,
            "category_slug": post.category.slug if post.category_id else None,
            "tags": [{"name": t.name, "slug": t.slug} for t in post.tags.all()],
            "author": post.author.full_name if post.author_id else "",
            "published_at": post.published_at.isoformat() if post.published_at else None,
        }

    def serialize_post_detail(self, post: BlogPost) -> dict:
        return {
            **self.serialize_post_list(post),
            "content": post.content,
            "seo": self.cms.serialize_seo(post),
        }

    def serialize_category(self, category: BlogCategory) -> dict:
        return {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
        }

    def serialize_tag(self, tag: BlogTag) -> dict:
        return {"id": tag.id, "name": tag.name, "slug": tag.slug}

    def serialize_comment(self, comment: BlogComment, include_replies: bool = True) -> dict:
        data = {
            "id": comment.id,
            "user": {"full_name": comment.user.full_name or comment.user.phone},
            "body": comment.body,
            "status": comment.status,
            "created_at": comment.created_at.isoformat(),
            "replies": [],
        }
        if include_replies:
            replies = comment.replies.filter(status=CommentStatus.APPROVED).select_related("user")
            data["replies"] = [self.serialize_comment(r, include_replies=False) for r in replies]
        return data
