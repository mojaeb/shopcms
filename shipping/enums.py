"""Shipping enumerations."""

from django.db import models


class ShippingProviderType(models.TextChoices):
    POST = "post", "پست"
    TIPAX = "tipax", "تیپاکس"
    PEYK = "peyk", "پیک"
    FREE = "free", "ارسال رایگان"
    API = "api", "API خارجی"


class CalculationMode(models.TextChoices):
    FIXED = "fixed", "ثابت"
    DISTANCE = "distance", "مسافت"
    WEIGHT = "weight", "وزن"
    DISTANCE_WEIGHT = "distance_weight", "مسافت + وزن"
    API = "api", "API"
