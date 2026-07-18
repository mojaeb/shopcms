"""Subscription models."""

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from orders.models import Order
from products.models import Product
from subscriptions.enums import BillingInterval, RenewalStatus, SubscriptionStatus
from tenants.models import Store


class SubscriptionPlan(TimeStampedModel):
    """Recurring billing plan for a product."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="subscription_plans", verbose_name="فروشگاه")
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name="subscription_plan",
        verbose_name="محصول",
    )
    interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
        verbose_name="دوره",
    )
    interval_count = models.PositiveIntegerField(default=1, verbose_name="تعداد دوره")
    trial_days = models.PositiveIntegerField(default=0, verbose_name="روز آزمایشی")
    grace_period_days = models.PositiveIntegerField(default=3, verbose_name="مهلت تمدید")
    price = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="قیمت")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "پلن اشتراک"
        verbose_name_plural = "پلن‌های اشتراک"

    def __str__(self):
        return f"{self.product.name} ({self.interval})"


class CustomerSubscription(TimeStampedModel):
    """Active or historical customer subscription."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="subscriptions", verbose_name="فروشگاه")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="کاربر",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="customer_subscriptions",
        verbose_name="محصول",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
        verbose_name="پلن",
    )
    initial_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subscriptions",
        verbose_name="سفارش اولیه",
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
        verbose_name="وضعیت",
    )
    interval = models.CharField(max_length=20, choices=BillingInterval.choices, verbose_name="دوره")
    interval_count = models.PositiveIntegerField(default=1, verbose_name="تعداد دوره")
    price = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="قیمت")
    auto_renew = models.BooleanField(default=True, verbose_name="تمدید خودکار")
    started_at = models.DateTimeField(verbose_name="شروع")
    current_period_start = models.DateTimeField(verbose_name="شروع دوره جاری")
    current_period_end = models.DateTimeField(verbose_name="پایان دوره جاری")
    trial_ends_at = models.DateTimeField(null=True, blank=True, verbose_name="پایان آزمایشی")
    canceled_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان لغو")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="انقضا نهایی")
    renewal_count = models.PositiveIntegerField(default=0, verbose_name="تعداد تمدید")

    class Meta:
        verbose_name = "اشتراک مشتری"
        verbose_name_plural = "اشتراک‌های مشتری"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "user"]),
            models.Index(fields=["status", "current_period_end"]),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.product.name}:{self.status}"


class SubscriptionRenewal(TimeStampedModel):
    """Renewal attempt history."""

    subscription = models.ForeignKey(
        CustomerSubscription,
        on_delete=models.CASCADE,
        related_name="renewals",
        verbose_name="اشتراک",
    )
    period_start = models.DateTimeField(verbose_name="شروع دوره")
    period_end = models.DateTimeField(verbose_name="پایان دوره")
    amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ")
    status = models.CharField(
        max_length=20,
        choices=RenewalStatus.choices,
        default=RenewalStatus.SUCCESS,
        verbose_name="وضعیت",
    )
    payment_ref = models.CharField(max_length=100, blank=True, verbose_name="مرجع پرداخت")
    note = models.CharField(max_length=255, blank=True, verbose_name="یادداشت")

    class Meta:
        verbose_name = "تمدید اشتراک"
        verbose_name_plural = "تمدیدهای اشتراک"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subscription_id}:{self.status}"
