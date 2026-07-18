"""Media file models."""

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from files.enums import FileType, StorageDriver, ThumbnailVariant
from tenants.models import Store


class MediaFile(TimeStampedModel):
    """Uploaded media asset scoped to a store."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="media_files",
        verbose_name="فروشگاه",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_files",
        verbose_name="آپلودکننده",
    )
    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
        verbose_name="نوع",
    )
    original_name = models.CharField(max_length=255, verbose_name="نام اصلی")
    storage_path = models.CharField(max_length=500, verbose_name="مسیر ذخیره")
    storage_driver = models.CharField(
        max_length=20,
        choices=StorageDriver.choices,
        default=StorageDriver.LOCAL,
        verbose_name="درایور",
    )
    mime_type = models.CharField(max_length=100, blank=True, verbose_name="MIME")
    size_bytes = models.PositiveBigIntegerField(default=0, verbose_name="حجم")
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name="عرض")
    height = models.PositiveIntegerField(null=True, blank=True, verbose_name="ارتفاع")
    url = models.URLField(max_length=500, verbose_name="آدرس")
    folder = models.CharField(max_length=200, blank=True, verbose_name="پوشه")
    title = models.CharField(max_length=200, blank=True, verbose_name="عنوان")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="متن جایگزین")
    is_public = models.BooleanField(default=True, verbose_name="عمومی")

    class Meta:
        verbose_name = "فایل"
        verbose_name_plural = "فایل‌ها"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "file_type"]),
            models.Index(fields=["store", "folder"]),
        ]

    def __str__(self):
        return self.original_name


class FileThumbnail(TimeStampedModel):
    """Generated image thumbnail variants."""

    media_file = models.ForeignKey(
        MediaFile,
        on_delete=models.CASCADE,
        related_name="thumbnails",
        verbose_name="فایل",
    )
    variant = models.CharField(
        max_length=20,
        choices=ThumbnailVariant.choices,
        verbose_name="اندازه",
    )
    storage_path = models.CharField(max_length=500, verbose_name="مسیر ذخیره")
    url = models.URLField(max_length=500, verbose_name="آدرس")
    width = models.PositiveIntegerField(default=0, verbose_name="عرض")
    height = models.PositiveIntegerField(default=0, verbose_name="ارتفاع")
    size_bytes = models.PositiveBigIntegerField(default=0, verbose_name="حجم")

    class Meta:
        verbose_name = "Thumbnail"
        verbose_name_plural = "Thumbnailها"
        unique_together = [("media_file", "variant")]
        ordering = ["variant"]

    def __str__(self):
        return f"{self.media_file_id}:{self.variant}"
