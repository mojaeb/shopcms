"""Store type and status enumerations."""

from django.db import models


class StoreType(models.TextChoices):
    PHYSICAL = "physical", "کالای فیزیکی + پست"
    DIGITAL_DOWNLOAD = "digital_download", "کالای دیجیتال + دانلود"
    SUBSCRIPTION = "subscription", "کالای دیجیتال + اشتراک"
    BOOKING = "booking", "رزرو + خرید خدمت"
    APPOINTMENT = "appointment", "رزرو + نوبت"
    RENTAL = "rental", "اجاره"
    PRINT_ON_DEMAND = "print_on_demand", "کالای سفارشی"


class StoreStatus(models.TextChoices):
    ACTIVE = "active", "فعال"
    INACTIVE = "inactive", "غیرفعال"
    SUSPENDED = "suspended", "معلق"


class SettingValueType(models.TextChoices):
    STRING = "string", "متن"
    INTEGER = "integer", "عدد صحیح"
    FLOAT = "float", "عدد اعشاری"
    BOOLEAN = "boolean", "بولین"
    JSON = "json", "JSON"
