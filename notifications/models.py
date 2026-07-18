"""Notification models."""

from django.db import models

from core.models import TimeStampedModel
from notifications.enums import ChannelType, NotificationStatus
from tenants.models import Store


class NotificationChannel(TimeStampedModel):
    """Per-store notification channel configuration."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="notification_channels",
        verbose_name="فروشگاه",
    )
    channel_type = models.CharField(max_length=20, choices=ChannelType.choices, verbose_name="نوع")
    provider = models.CharField(max_length=50, verbose_name="ارائه‌دهنده")
    config = models.JSONField(default=dict, blank=True, verbose_name="تنظیمات")
    is_default = models.BooleanField(default=False, verbose_name="پیش‌فرض")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "کانال اعلان"
        verbose_name_plural = "کانال‌های اعلان"
        unique_together = [("store", "channel_type", "provider")]
        ordering = ["channel_type", "provider"]

    def __str__(self):
        return f"{self.store.slug}:{self.channel_type}:{self.provider}"


class NotificationLog(TimeStampedModel):
    """Audit log for sent notifications."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_logs",
        verbose_name="فروشگاه",
    )
    channel_type = models.CharField(max_length=20, choices=ChannelType.choices, verbose_name="نوع")
    provider = models.CharField(max_length=50, verbose_name="ارائه‌دهنده")
    recipient = models.CharField(max_length=255, verbose_name="گیرنده")
    subject = models.CharField(max_length=255, blank=True, verbose_name="موضوع")
    body = models.TextField(verbose_name="متن")
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        verbose_name="وضعیت",
    )
    metadata = models.JSONField(default=dict, blank=True, verbose_name="متادیتا")
    error_message = models.TextField(blank=True, verbose_name="خطا")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان ارسال")

    class Meta:
        verbose_name = "لاگ اعلان"
        verbose_name_plural = "لاگ‌های اعلان"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "channel_type"]),
            models.Index(fields=["recipient"]),
        ]

    def __str__(self):
        return f"{self.channel_type}:{self.recipient}:{self.status}"
