"""File enums."""

from django.db import models


class FileType(models.TextChoices):
    IMAGE = "image", "تصویر"
    VIDEO = "video", "ویدیو"
    DOCUMENT = "document", "سند"
    OTHER = "other", "سایر"


class StorageDriver(models.TextChoices):
    LOCAL = "local", "Local"
    S3 = "s3", "Amazon S3"
    MINIO = "minio", "MinIO"
    R2 = "r2", "Cloudflare R2"


class ThumbnailVariant(models.TextChoices):
    THUMB = "thumb", "Thumbnail"
    SMALL = "small", "Small"
    MEDIUM = "medium", "Medium"
    LARGE = "large", "Large"
