"""Tax models."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimeStampedModel
from products.models import Category, Product
from taxes.enums import TaxRuleScope
from tenants.models import Store


class TaxRule(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="tax_rules", verbose_name="فروشگاه")
    name = models.CharField(max_length=200, verbose_name="نام")
    rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="درصد مالیات",
    )
    scope = models.CharField(max_length=20, choices=TaxRuleScope.choices, default=TaxRuleScope.ALL, verbose_name="محدوده")
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tax_rules",
        verbose_name="دسته‌بندی",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tax_rules",
        verbose_name="محصول",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    priority = models.IntegerField(default=0, verbose_name="اولویت")

    class Meta:
        verbose_name = "قانون مالیات"
        verbose_name_plural = "قوانین مالیات"
        ordering = ["-priority", "name"]

    def __str__(self):
        return f"{self.name} ({self.rate_percent}%)"
