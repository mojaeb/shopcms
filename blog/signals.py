"""Blog cache invalidation signals."""

from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from blog.models import BlogCategory, BlogComment, BlogPost, BlogTag
from comments.enums import CommentStatus
from core.cache import cache_manager


def _invalidate(store_id: int | None) -> None:
    if store_id:
        cache_manager.invalidate_blog(store_id)


@receiver(post_save, sender=BlogPost)
@receiver(post_delete, sender=BlogPost)
def invalidate_on_post(sender, instance, **kwargs):
    _invalidate(instance.store_id)


@receiver(post_save, sender=BlogCategory)
@receiver(post_delete, sender=BlogCategory)
def invalidate_on_category(sender, instance, **kwargs):
    _invalidate(instance.store_id)


@receiver(post_save, sender=BlogTag)
@receiver(post_delete, sender=BlogTag)
def invalidate_on_tag(sender, instance, **kwargs):
    _invalidate(instance.store_id)


@receiver(m2m_changed, sender=BlogPost.tags.through)
def invalidate_on_post_tags(sender, instance, **kwargs):
    _invalidate(getattr(instance, "store_id", None))


@receiver(post_save, sender=BlogComment)
@receiver(post_delete, sender=BlogComment)
def invalidate_on_comment(sender, instance, **kwargs):
    store_id = getattr(instance, "store_id", None)
    if not store_id and getattr(instance, "post_id", None):
        store_id = instance.post.store_id
    # Bust when approved comments change (or any delete of an approved comment).
    if instance.status == CommentStatus.APPROVED:
        _invalidate(store_id)
