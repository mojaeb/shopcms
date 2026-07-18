"""Payment models."""

import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimeStampedModel
from payments.enums import GatewayType, PaymentStatus
from tenants.models import Store


def generate_tracking_code() -> str:
    return secrets.token_hex(8).upper()


class PaymentTransaction(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="payments", verbose_name="فروشگاه")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="کاربر",
    )
    gateway = models.CharField(max_length=20, choices=GatewayType.choices, verbose_name="درگاه")
    amount = models.DecimalField(max_digits=12, decimal_places=0, validators=[MinValueValidator(0)], verbose_name="مبلغ")
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name="وضعیت",
    )
    tracking_code = models.CharField(max_length=32, unique=True, default=generate_tracking_code, verbose_name="کد پیگیری")
    authority = models.CharField(max_length=100, blank=True, db_index=True, verbose_name="Authority")
    ref_id = models.CharField(max_length=100, blank=True, verbose_name="Ref ID")
    payment_url = models.URLField(blank=True, verbose_name="آدرس پرداخت")
    callback_url = models.CharField(max_length=500, blank=True, verbose_name="Callback")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="متادیتا")
    verify_data = models.JSONField(default=dict, blank=True, verbose_name="پاسخ تایید")
    error_message = models.TextField(blank=True, verbose_name="خطا")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان پرداخت")
    refunded_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="مبلغ بازگشت",
    )

    class Meta:
        verbose_name = "تراکنش پرداخت"
        verbose_name_plural = "تراکنش‌های پرداخت"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["store", "created_at"]),
        ]

    def __str__(self):
        return f"{self.tracking_code} - {self.gateway} - {self.status}"
