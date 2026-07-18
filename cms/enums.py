"""CMS enumerations."""

from django.db import models


class MenuLocation(models.TextChoices):
    HEADER = "header", "هدر"
    FOOTER = "footer", "فوتر"
    SIDEBAR = "sidebar", "سایدبار"


class BannerPosition(models.TextChoices):
    HOME_TOP = "home_top", "بالای صفحه خانه"
    HOME_MIDDLE = "home_middle", "وسط صفحه خانه"
    CATEGORY_TOP = "category_top", "بالای دسته‌بندی"
    SIDEBAR = "sidebar", "سایدبار"


class WidgetType(models.TextChoices):
    HTML = "html", "HTML"
    TEXT = "text", "متن"
    IMAGE = "image", "تصویر"
    PRODUCT_LIST = "product_list", "لیست محصولات"
    BANNER = "banner", "بنر"


class BlockType(models.TextChoices):
    HERO = "hero", "هیرو"
    TEXT = "text", "متن"
    IMAGE = "image", "تصویر"
    HTML = "html", "HTML"
    WIDGET = "widget", "ویجت"
