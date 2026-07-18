"""Comment and review models."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from comments.enums import CommentStatus
from core.models import TimeStampedModel
from products.models import Product
from tenants.models import Store


class Comment(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="comments", verbose_name="فروشگاه")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="comments", verbose_name="محصول")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_comments",
        verbose_name="کاربر",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="پاسخ به",
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="امتیاز",
    )
    body = models.TextField(verbose_name="متن")
    status = models.CharField(
        max_length=20,
        choices=CommentStatus.choices,
        default=CommentStatus.PENDING,
        verbose_name="وضعیت",
    )
    likes_count = models.PositiveIntegerField(default=0, verbose_name="تعداد لایک")
    is_verified_purchase = models.BooleanField(default=False, verbose_name="خرید تایید شده")

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} - {self.user_id}"


class CommentLike(TimeStampedModel):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes", verbose_name="نظر")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comment_likes",
        verbose_name="کاربر",
    )

    class Meta:
        verbose_name = "لایک نظر"
        verbose_name_plural = "لایک‌های نظر"
        unique_together = [("comment", "user")]

    def __str__(self):
        return f"{self.user_id} -> {self.comment_id}"
