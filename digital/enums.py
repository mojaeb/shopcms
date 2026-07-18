"""Digital download enums."""

from django.db import models


class LicenseStatus(models.TextChoices):
    ACTIVE = "active", "فعال"
    EXPIRED = "expired", "منقضی"
    EXHAUSTED = "exhausted", "اتمام دانلود"
    REVOKED = "revoked", "لغو شده"
