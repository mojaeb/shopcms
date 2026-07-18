"""Subscription enums."""

from django.db import models


class BillingInterval(models.TextChoices):
    WEEKLY = "weekly", "هفتگی"
    MONTHLY = "monthly", "ماهانه"
    YEARLY = "yearly", "سالانه"


class SubscriptionStatus(models.TextChoices):
    TRIALING = "trialing", "دوره آزمایشی"
    ACTIVE = "active", "فعال"
    PAST_DUE = "past_due", "معوق"
    CANCELED = "canceled", "لغو شده"
    EXPIRED = "expired", "منقضی"


class RenewalStatus(models.TextChoices):
    SUCCESS = "success", "موفق"
    FAILED = "failed", "ناموفق"
    PENDING = "pending", "در انتظار"
