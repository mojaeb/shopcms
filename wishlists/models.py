"""Wishlist models."""

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from products.models import Product
from tenants.models import Store


class WishlistItem(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="wishlist_items", verbose_name="فروشگاه")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name="کاربر",
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlist_items", verbose_name="محصول")

    class Meta:
        verbose_name = "علاقه‌مندی"
        verbose_name_plural = "علاقه‌مندی‌ها"
        unique_together = [("store", "user", "product")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} - {self.product.name}"
