"""Tax enumerations."""

from django.db import models


class TaxRuleScope(models.TextChoices):
    ALL = "all", "همه محصولات"
    CATEGORY = "category", "دسته‌بندی"
    PRODUCT = "product", "محصول"
