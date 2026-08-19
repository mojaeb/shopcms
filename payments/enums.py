"""Payment enumerations."""

from django.db import models


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "در انتظار"
    REDIRECTED = "redirected", "انتقال به درگاه"
    PAID = "paid", "پرداخت شده"
    FAILED = "failed", "ناموفق"
    REFUNDED = "refunded", "بازگشت وجه"
    CANCELLED = "cancelled", "لغو شده"


class GatewayType(models.TextChoices):
    ZARINPAL = "zarinpal", "زرین‌پال"
    IDPAY = "idpay", "آیدی‌پی"
    MELLAT = "mellat", "ملت"
    PASARGAD = "pasargad", "پاسارگاد"
    SINA = "sina", "سینا"
