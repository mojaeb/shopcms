"""Comment service layer."""

import logging

from django.db import transaction
from django.db.models import Avg, Count

from comments.enums import CommentStatus
from comments.models import Comment, CommentLike
from orders.enums import OrderStatus
from orders.models import OrderItem
from products.enums import ProductStatus
from products.models import Product
from tenants.models import StorePlugin

logger = logging.getLogger(__name__)


class CommentError(Exception):
    pass


class CommentService:
    """Product reviews, replies, likes, and moderation."""

    PAID_STATUSES = [
        OrderStatus.PAID,
        OrderStatus.PREPARING,
        OrderStatus.SENT,
        OrderStatus.DELIVERED,
    ]

    def is_active(self, store) -> bool:
        from plugins.services.plugin import PluginService

        return PluginService().is_enabled(store, "comments")

    def list_product_comments(self, store, product_slug: str, user=None):
        product = self._get_product(store, product_slug)
        qs = (
            Comment.objects.filter(
                store=store,
                product=product,
                parent__isnull=True,
                status=CommentStatus.APPROVED,
            )
            .select_related("user")
            .prefetch_related("replies__user")
            .order_by("-created_at")
        )
        return qs

    def get_product_summary(self, store, product_slug: str) -> dict:
        product = self._get_product(store, product_slug)
        agg = Comment.objects.filter(
            store=store,
            product=product,
            parent__isnull=True,
            status=CommentStatus.APPROVED,
            rating__isnull=False,
        ).aggregate(avg=Avg("rating"), count=Count("id"))
        return {
            "average_rating": round(float(agg["avg"] or 0), 1),
            "review_count": agg["count"] or 0,
        }

    def list_user_comments(self, user, store):
        return (
            Comment.objects.filter(store=store, user=user, parent__isnull=True)
            .select_related("product")
            .order_by("-created_at")
        )

    def list_store_comments(self, store, status: str | None = None, *, top_level_only: bool = False):
        qs = Comment.objects.filter(store=store).select_related("user", "product", "parent")
        if top_level_only:
            qs = qs.filter(parent__isnull=True)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")

    @transaction.atomic
    def create_comment(
        self,
        user,
        store,
        product_slug: str,
        body: str,
        rating: int | None = None,
        parent_id: int | None = None,
    ) -> Comment:
        if not self.is_active(store):
            raise CommentError("نظرات برای این فروشگاه فعال نیست")

        body = body.strip()
        if len(body) < 3:
            raise CommentError("متن نظر خیلی کوتاه است")

        product = self._get_product(store, product_slug)
        parent = None

        if parent_id:
            try:
                parent = Comment.objects.get(pk=parent_id, store=store, product=product)
            except Comment.DoesNotExist:
                raise CommentError("نظر والد یافت نشد")
            if parent.parent_id:
                raise CommentError("فقط یک سطح پاسخ مجاز است")
            # Replies to pending parents are fine; both need moderation.
            rating = None
        elif rating is not None and (rating < 1 or rating > 5):
            raise CommentError("امتیاز باید بین ۱ تا ۵ باشد")

        comment = Comment.objects.create(
            store=store,
            product=product,
            user=user,
            parent=parent,
            rating=rating,
            body=body,
            status=CommentStatus.PENDING,
            is_verified_purchase=self._has_purchased(user, store, product),
        )
        logger.info("Comment created: product=%s user=%s status=pending", product.slug, user.pk)
        return comment

    @transaction.atomic
    def toggle_like(self, user, store, comment_id: int) -> dict:
        try:
            comment = Comment.objects.get(pk=comment_id, store=store, status=CommentStatus.APPROVED)
        except Comment.DoesNotExist:
            raise CommentError("نظر یافت نشد")

        like, created = CommentLike.objects.get_or_create(comment=comment, user=user)
        if not created:
            like.delete()
            comment.likes_count = max(0, comment.likes_count - 1)
            comment.save(update_fields=["likes_count", "updated_at"])
            return {"liked": False, "likes_count": comment.likes_count}

        comment.likes_count += 1
        comment.save(update_fields=["likes_count", "updated_at"])
        return {"liked": True, "likes_count": comment.likes_count}

    @transaction.atomic
    def moderate_comment(self, store, comment_id: int, status: str) -> Comment:
        if status not in CommentStatus.values:
            raise CommentError("وضعیت نامعتبر است")

        try:
            comment = Comment.objects.select_related("user", "product", "parent").get(
                pk=comment_id, store=store
            )
        except Comment.DoesNotExist:
            raise CommentError("نظر یافت نشد")

        comment.status = status
        comment.save(update_fields=["status", "updated_at"])
        return comment

    def get_pending_count(self, store) -> int:
        return Comment.objects.filter(store=store, status=CommentStatus.PENDING).count()

    def serialize_comment(
        self,
        comment: Comment,
        user=None,
        include_replies: bool = True,
        *,
        for_admin: bool = False,
    ) -> dict:
        data = {
            "id": comment.id,
            "product_id": comment.product_id,
            "product_name": comment.product.name if getattr(comment, "product", None) else "",
            "product_slug": comment.product.slug if getattr(comment, "product", None) else "",
            "parent_id": comment.parent_id,
            "user": {
                "id": comment.user_id,
                "full_name": comment.user.full_name or comment.user.phone,
            },
            "rating": comment.rating,
            "body": comment.body,
            "status": comment.status,
            "status_label": comment.get_status_display(),
            "likes_count": comment.likes_count,
            "is_verified_purchase": comment.is_verified_purchase,
            "liked_by_me": False,
            "created_at": comment.created_at.isoformat(),
            "replies": [],
        }

        if user and user.is_authenticated:
            data["liked_by_me"] = CommentLike.objects.filter(comment=comment, user=user).exists()

        if include_replies:
            replies = comment.replies.select_related("user").order_by("created_at")
            if not for_admin:
                replies = replies.filter(status=CommentStatus.APPROVED)
            data["replies"] = [
                self.serialize_comment(r, user, include_replies=False, for_admin=for_admin)
                for r in replies
            ]

        return data

    def _get_product(self, store, product_slug: str) -> Product:
        product = Product.objects.filter(store=store, slug=product_slug, status=ProductStatus.ACTIVE).first()
        if not product:
            raise CommentError("محصول یافت نشد")
        return product

    def _has_purchased(self, user, store, product: Product) -> bool:
        return OrderItem.objects.filter(
            order__store=store,
            order__user=user,
            order__status__in=self.PAID_STATUSES,
            product_id=product.id,
        ).exists()
