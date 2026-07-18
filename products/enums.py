"""Product enumerations."""

from django.db import models


class ProductStatus(models.TextChoices):
    DRAFT = "draft", "پیش‌نویس"
    ACTIVE = "active", "فعال"
    INACTIVE = "inactive", "غیرفعال"


class ProductType(models.TextChoices):
    SIMPLE = "simple", "ساده"
    VARIABLE = "variable", "متغیر"
    DIGITAL = "digital", "دیجیتال"
    SUBSCRIPTION = "subscription", "اشتراک"


class AttributeDisplayType(models.TextChoices):
    LIST = "list", "لیست"
    SELECT = "select", "انتخاب"
    COLOR = "color", "رنگ"
    BUTTON = "button", "دکمه"


class ButtonDisplayStyle(models.TextChoices):
    ICON = "icon", "فقط آیکون"
    TEXT = "text", "فقط متن"
    ICON_TEXT = "icon_text", "آیکون + متن"


class ProductSortOrder(models.TextChoices):
    NEWEST = "newest", "جدیدترین"
    OLDEST = "oldest", "قدیمی‌ترین"
    PRICE_ASC = "price_asc", "ارزان‌ترین"
    PRICE_DESC = "price_desc", "گران‌ترین"
    NAME_ASC = "name_asc", "نام (الف-ی)"
    NAME_DESC = "name_desc", "نام (ی-الف)"
    FEATURED = "featured", "ویژه"
