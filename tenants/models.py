"""Tenant models."""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimeStampedModel
from tenants.enums import SettingValueType, StoreStatus, StoreType


class Theme(TimeStampedModel):
    """Theme definition for storefront rendering."""

    name = models.CharField(max_length=100, verbose_name="نام")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="شناسه")
    directory = models.CharField(
        max_length=200,
        help_text="نام پوشه تم در themes/ (مثلاً modern)",
        verbose_name="پوشه",
    )
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_default = models.BooleanField(default=False, verbose_name="پیش‌فرض")

    class Meta:
        verbose_name = "تم"
        verbose_name_plural = "تم‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            Theme.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Store(TimeStampedModel):
    """Multi-tenant store instance."""

    name = models.CharField(max_length=200, verbose_name="نام فروشگاه")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="شناسه")
    store_type = models.CharField(
        max_length=30,
        choices=StoreType.choices,
        default=StoreType.PHYSICAL,
        verbose_name="نوع فروشگاه",
    )
    theme = models.ForeignKey(
        Theme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stores",
        verbose_name="تم",
    )
    default_theme = models.ForeignKey(
        Theme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_stores",
        help_text="تم پیش‌فرض در صورت نبود تم اختصاصی",
        verbose_name="تم پیش‌فرض",
    )
    currency = models.CharField(max_length=10, default="IRR", verbose_name="ارز")
    timezone = models.CharField(max_length=50, default="Asia/Tehran", verbose_name="منطقه زمانی")
    language = models.CharField(max_length=10, default="fa", verbose_name="زبان")
    status = models.CharField(
        max_length=20,
        choices=StoreStatus.choices,
        default=StoreStatus.ACTIVE,
        verbose_name="وضعیت",
    )
    tax_enabled = models.BooleanField(default=False, verbose_name="مالیات فعال")
    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="درصد مالیات",
    )

    class Meta:
        verbose_name = "فروشگاه"
        verbose_name_plural = "فروشگاه‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_active(self) -> bool:
        return self.status == StoreStatus.ACTIVE

    @property
    def effective_theme(self) -> Theme | None:
        return self.theme or self.default_theme

    @property
    def effective_theme_slug(self) -> str:
        theme = self.effective_theme
        return theme.directory if theme else "default"


class Domain(TimeStampedModel):
    """Domain mapping to a store."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="domains",
        verbose_name="فروشگاه",
    )
    domain = models.CharField(
        max_length=255,
        unique=True,
        help_text="مثلاً shop1.com یا shop.example.com",
        verbose_name="دامنه",
    )
    is_primary = models.BooleanField(default=False, verbose_name="دامنه اصلی")
    ssl_enabled = models.BooleanField(default=True, verbose_name="SSL فعال")
    redirect_to_primary = models.BooleanField(
        default=False,
        help_text="در صورت فعال بودن به دامنه اصلی ریدایرکت شود",
        verbose_name="ریدایرکت به دامنه اصلی",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "دامنه"
        verbose_name_plural = "دامنه‌ها"
        ordering = ["-is_primary", "domain"]

    def __str__(self):
        return self.domain

    def save(self, *args, **kwargs):
        self.domain = self.domain.lower().strip()
        if self.is_primary:
            Domain.objects.filter(store=self.store, is_primary=True).exclude(pk=self.pk).update(
                is_primary=False
            )
        super().save(*args, **kwargs)


class StoreSetting(TimeStampedModel):
    """Key-value settings per store with schema support."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="settings",
        verbose_name="فروشگاه",
    )
    group = models.CharField(
        max_length=100,
        default="general",
        help_text="مثلاً payment, shipping, theme",
        verbose_name="گروه",
    )
    key = models.CharField(max_length=200, verbose_name="کلید")
    # blank=True: empty JSON string "" is a valid stored value (contact/seo clears),
    # and Django's forms.JSONField treats "" as empty — without blank, admin save fails.
    value = models.JSONField(default=dict, blank=True, verbose_name="مقدار")
    value_type = models.CharField(
        max_length=20,
        choices=SettingValueType.choices,
        default=SettingValueType.JSON,
        verbose_name="نوع مقدار",
    )
    description = models.CharField(max_length=500, blank=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "تنظیمات فروشگاه"
        verbose_name_plural = "تنظیمات فروشگاه‌ها"
        unique_together = [("store", "group", "key")]
        ordering = ["group", "key"]

    def __str__(self):
        return f"{self.store.slug}.{self.group}.{self.key}"

    @property
    def dotted_key(self) -> str:
        return f"{self.group}.{self.key}"


class Plugin(TimeStampedModel):
    """Platform plugin definition."""

    codename = models.SlugField(max_length=50, unique=True, verbose_name="شناسه")
    name = models.CharField(max_length=100, verbose_name="نام")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    compatible_store_types = models.JSONField(
        default=list,
        blank=True,
        help_text="لیست خالی = سازگار با همه انواع فروشگاه",
        verbose_name="انواع فروشگاه سازگار",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_system = models.BooleanField(default=True, verbose_name="سیستمی")

    class Meta:
        verbose_name = "افزونه"
        verbose_name_plural = "افزونه‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def is_compatible_with(self, store_type: str) -> bool:
        if not self.compatible_store_types:
            return True
        return store_type in self.compatible_store_types


class StorePlugin(TimeStampedModel):
    """Plugin enabled/disabled per store."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="plugins",
        verbose_name="فروشگاه",
    )
    plugin = models.ForeignKey(
        Plugin,
        on_delete=models.CASCADE,
        related_name="store_plugins",
        verbose_name="افزونه",
    )
    is_enabled = models.BooleanField(default=True, verbose_name="فعال")
    settings = models.JSONField(default=dict, blank=True, verbose_name="تنظیمات")

    class Meta:
        verbose_name = "افزونه فروشگاه"
        verbose_name_plural = "افزونه‌های فروشگاه"
        unique_together = [("store", "plugin")]
        ordering = ["plugin__name"]

    def __str__(self):
        status = "on" if self.is_enabled else "off"
        return f"{self.store.slug} - {self.plugin.codename} ({status})"

