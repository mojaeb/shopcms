"""Core models - base abstractions for the platform."""

from django.db import models

from core.enums import AuditAction, AuditOutcome, BackupScope, BackupStatus


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Abstract base model with soft delete support."""

    is_deleted = models.BooleanField(default=False, verbose_name="حذف شده")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ حذف")

    class Meta:
        abstract = True


class BackupJob(TimeStampedModel):
    """Tracks store and platform backup jobs."""

    store = models.ForeignKey(
        "tenants.Store",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="backup_jobs",
        verbose_name="فروشگاه",
    )
    scope = models.CharField(
        max_length=20,
        choices=BackupScope.choices,
        default=BackupScope.STORE,
        verbose_name="محدوده",
    )
    status = models.CharField(
        max_length=20,
        choices=BackupStatus.choices,
        default=BackupStatus.PENDING,
        verbose_name="وضعیت",
    )
    file_path = models.CharField(max_length=500, blank=True, verbose_name="مسیر فایل")
    file_size = models.BigIntegerField(default=0, verbose_name="حجم فایل")
    include_media = models.BooleanField(default=True, verbose_name="شامل رسانه")
    record_count = models.PositiveIntegerField(default=0, verbose_name="تعداد رکورد")
    checksum = models.CharField(max_length=64, blank=True, verbose_name="Checksum")
    error_message = models.TextField(blank=True, verbose_name="خطا")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان اتمام")

    class Meta:
        verbose_name = "بکاپ"
        verbose_name_plural = "بکاپ‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        target = self.store.slug if self.store_id else "platform"
        return f"{target} - {self.status}"


class AuditLog(TimeStampedModel):
    """Security and authentication audit trail."""

    store = models.ForeignKey(
        "tenants.Store",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="فروشگاه",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="کاربر",
    )
    action = models.CharField(max_length=50, choices=AuditAction.choices, verbose_name="عملیات")
    outcome = models.CharField(
        max_length=20,
        choices=AuditOutcome.choices,
        default=AuditOutcome.SUCCESS,
        verbose_name="نتیجه",
    )
    resource_type = models.CharField(max_length=100, blank=True, verbose_name="نوع منبع")
    resource_id = models.CharField(max_length=100, blank=True, verbose_name="شناسه منبع")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.CharField(max_length=500, blank=True, verbose_name="User Agent")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="متادیتا")

    class Meta:
        verbose_name = "لاگ امنیتی"
        verbose_name_plural = "لاگ‌های امنیتی"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "action", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.outcome}"

