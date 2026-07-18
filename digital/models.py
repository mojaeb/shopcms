"""Digital product and download license models."""

import secrets

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from digital.enums import LicenseStatus
from files.models import MediaFile
from orders.models import Order, OrderItem
from products.models import Product
from tenants.models import Store


def generate_download_token() -> str:
    return secrets.token_urlsafe(32)


class ProductDigitalAsset(TimeStampedModel):
    """Digital file attached to a product."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="digital_assets", verbose_name="فروشگاه")
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="digital_assets",
        verbose_name="محصول",
    )
    media_file = models.ForeignKey(
        MediaFile,
        on_delete=models.CASCADE,
        related_name="digital_assets",
        verbose_name="فایل",
    )
    title = models.CharField(max_length=200, blank=True, verbose_name="عنوان")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")
    max_downloads = models.PositiveIntegerField(null=True, blank=True, verbose_name="حداکثر دانلود")
    expire_hours = models.PositiveIntegerField(null=True, blank=True, verbose_name="انقضا (ساعت)")

    class Meta:
        verbose_name = "فایل دیجیتال محصول"
        verbose_name_plural = "فایل‌های دیجیتال محصول"
        unique_together = [("product", "media_file")]
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title or self.media_file.original_name


class DownloadLicense(TimeStampedModel):
    """Download entitlement after purchase."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="download_licenses", verbose_name="فروشگاه")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="download_licenses",
        verbose_name="کاربر",
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="download_licenses", verbose_name="سفارش")
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="download_licenses",
        verbose_name="آیتم سفارش",
    )
    product_id = models.IntegerField(verbose_name="شناسه محصول")
    media_file = models.ForeignKey(
        MediaFile,
        on_delete=models.PROTECT,
        related_name="download_licenses",
        verbose_name="فایل",
    )
    token = models.CharField(max_length=64, unique=True, default=generate_download_token, verbose_name="توکن")
    max_downloads = models.PositiveIntegerField(default=5, verbose_name="حداکثر دانلود")
    download_count = models.PositiveIntegerField(default=0, verbose_name="تعداد دانلود")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انقضا")
    status = models.CharField(
        max_length=20,
        choices=LicenseStatus.choices,
        default=LicenseStatus.ACTIVE,
        verbose_name="وضعیت",
    )
    last_download_at = models.DateTimeField(null=True, blank=True, verbose_name="آخرین دانلود")

    class Meta:
        verbose_name = "مجوز دانلود"
        verbose_name_plural = "مجوزهای دانلود"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "user"]),
            models.Index(fields=["token"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.media_file.original_name}:{self.status}"
