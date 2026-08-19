"""Shipping models."""

from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimeStampedModel
from shipping.enums import CalculationMode, ShippingPaymentType, ShippingProviderType, ShippingZoneTier
from tenants.models import Store


class ShippingZone(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="shipping_zones", verbose_name="فروشگاه")
    name = models.CharField(max_length=200, verbose_name="نام")
    provinces = models.JSONField(default=list, blank=True, verbose_name="استان‌ها")
    cities = models.JSONField(default=list, blank=True, verbose_name="شهرها")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "منطقه ارسال"
        verbose_name_plural = "مناطق ارسال"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def matches(self, province: str, city: str) -> bool:
        if self.cities and city in self.cities:
            return True
        if self.provinces and province in self.provinces:
            return True
        return not self.cities and not self.provinces


class ShippingMethod(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="shipping_methods", verbose_name="فروشگاه")
    zone = models.ForeignKey(
        ShippingZone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="methods",
        verbose_name="منطقه",
    )
    name = models.CharField(max_length=200, verbose_name="نام")
    slug = models.SlugField(max_length=200, verbose_name="شناسه")
    provider = models.CharField(max_length=20, choices=ShippingProviderType.choices, verbose_name="ارائه‌دهنده")
    calculation_mode = models.CharField(max_length=20, choices=CalculationMode.choices, verbose_name="نوع محاسبه")
    config = models.JSONField(default=dict, blank=True, verbose_name="تنظیمات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")
    min_order_amount = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, validators=[MinValueValidator(0)], verbose_name="حداقل سفارش",
    )
    free_shipping_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="آستانه ارسال رایگان",
    )
    estimated_days = models.PositiveIntegerField(default=3, verbose_name="زمان تحویل (روز)")
    payment_type = models.CharField(
        max_length=10,
        choices=ShippingPaymentType.choices,
        default=ShippingPaymentType.PREPAID,
        verbose_name="نوع پرداخت کرایه",
    )

    class Meta:
        verbose_name = "روش ارسال"
        verbose_name_plural = "روش‌های ارسال"
        unique_together = [("store", "slug")]
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class ShippingPrice(TimeStampedModel):
    method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name="روش ارسال",
    )
    from_city = models.CharField(max_length=100, blank=True, verbose_name="شهر مبدا")
    to_city = models.CharField(max_length=100, blank=True, verbose_name="شهر مقصد")
    zone_tier = models.CharField(
        max_length=10,
        choices=ShippingZoneTier.choices,
        blank=True,
        verbose_name="سطح منطقه",
    )
    weight_min_kg = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)], verbose_name="حداقل وزن (کیلو)",
    )
    weight_max_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)], verbose_name="حداکثر وزن (کیلو)",
    )
    price = models.DecimalField(max_digits=12, decimal_places=0, validators=[MinValueValidator(0)], verbose_name="قیمت")
    extra_per_kg = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, validators=[MinValueValidator(0)], verbose_name="مازاد هر کیلو",
    )

    class Meta:
        verbose_name = "تعرفه ارسال"
        verbose_name_plural = "تعرفه‌های ارسال"
        ordering = ["from_city", "to_city", "weight_min_kg"]

    def __str__(self):
        return f"{self.from_city} → {self.to_city}: {self.price}"


class ShippingRule(TimeStampedModel):
    method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.CASCADE,
        related_name="rules",
        verbose_name="روش ارسال",
    )
    zone = models.ForeignKey(
        ShippingZone,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rules",
        verbose_name="منطقه",
    )
    name = models.CharField(max_length=200, verbose_name="نام")
    config = models.JSONField(default=dict, blank=True, verbose_name="تنظیمات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    priority = models.IntegerField(default=0, verbose_name="اولویت")

    class Meta:
        verbose_name = "قانون ارسال"
        verbose_name_plural = "قوانین ارسال"
        ordering = ["-priority", "id"]

    def __str__(self):
        return self.name
