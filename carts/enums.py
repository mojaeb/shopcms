"""Cart enumerations."""

from django.db import models


class DiscountType(models.TextChoices):
    PERCENTAGE = "percentage", "درصدی"
    FIXED = "fixed", "مبلغ ثابت"


class DiscountScope(models.TextChoices):
    ALL = "all", "همه محصولات"
    CATEGORY = "category", "دسته‌بندی"
    PRODUCT = "product", "محصول"
