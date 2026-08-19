"""Tenant admin configuration — unified store settings form (Unfold)."""

from __future__ import annotations

import json

from django import forms
from django.contrib import admin
from django.db.models import Prefetch, Q
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.widgets import UnfoldAdminTextareaWidget

from accounts.models import StoreMembership
from tenants.forms import StoreConfigForm
from tenants.models import Domain, Plugin, Store, StorePlugin, StoreSetting, Theme
from tenants.services.advanced_settings import (
    advanced_setting_description,
    ensure_advanced_setting_rows,
)
from shipping.models import ShippingMethod
from tenants.services.store_config import STRUCTURED_ADMIN_SETTING_KEYS


class DomainInline(TabularInline):
    model = Domain
    # extra=0: an empty row with default is_active=True is treated as "changed"
    # and then fails with required domain on every save.
    extra = 0
    tab = True
    verbose_name = "دامنه"
    verbose_name_plural = "دامنه‌ها"
    fields = ("domain", "is_primary", "ssl_enabled", "redirect_to_primary", "is_active")


class StorePluginInline(TabularInline):
    model = StorePlugin
    extra = 0
    tab = True
    verbose_name = "افزونه"
    verbose_name_plural = "افزونه‌ها"
    autocomplete_fields = ("plugin",)
    fields = ("plugin", "is_enabled", "settings")


class PrettyJSONTextarea(UnfoldAdminTextareaWidget):
    """Large LTR monospace textarea for editing JSON without guessing structure."""

    def __init__(self, attrs=None):
        defaults = {
            "rows": 18,
            "cols": 100,
            "dir": "ltr",
            "spellcheck": "false",
            "class": "vLargeTextField shopcms-pretty-json",
            "style": "font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; line-height: 1.45;",
        }
        if attrs:
            defaults.update(attrs)
        super().__init__(attrs=defaults)


class PrettyJSONFormField(forms.JSONField):
    """Show indented JSON; keep empty string as a valid blank value."""

    widget = PrettyJSONTextarea

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if value is None or value == "":
            return ""
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return ""
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                return value
        try:
            return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False)
        except (TypeError, ValueError):
            return str(value)


class _StoreSettingInlineForm(forms.ModelForm):
    """Pretty JSON editor; blank values allowed; description hints for known keys."""

    value = PrettyJSONFormField(label="مقدار", required=False)

    class Meta:
        model = StoreSetting
        fields = ("group", "key", "value", "value_type", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance and instance.pk:
            hint = advanced_setting_description(instance.group, instance.key)
            if hint:
                self.fields["value"].help_text = hint
                if not (instance.description or "").strip():
                    self.fields["description"].initial = hint
            self.fields["group"].widget.attrs.setdefault("readonly", True)
            self.fields["key"].widget.attrs.setdefault("readonly", True)

    def clean_value(self):
        value = self.cleaned_data.get("value")
        if value is None:
            return ""
        return value


class StoreSettingInline(StackedInline):
    """Raw key/value settings for theme.config and custom keys (form-owned keys are hidden)."""

    model = StoreSetting
    form = _StoreSettingInlineForm
    extra = 0
    tab = True
    collapsible = True
    verbose_name = "تنظیم پیشرفته"
    verbose_name_plural = "تنظیمات پیشرفته (JSON)"
    fields = ("group", "key", "description", "value", "value_type")
    readonly_fields = ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        exclude = Q()
        for group, key in STRUCTURED_ADMIN_SETTING_KEYS:
            exclude |= Q(group=group, key=key)
        qs = qs.exclude(exclude) if STRUCTURED_ADMIN_SETTING_KEYS else qs
        return qs.order_by("group", "key")


class _ShippingMethodInlineForm(forms.ModelForm):
    config = PrettyJSONFormField(
        label="تنظیمات (JSON)",
        required=False,
        widget=PrettyJSONTextarea(attrs={"rows": 8}),
    )

    class Meta:
        model = ShippingMethod
        fields = (
            "name",
            "slug",
            "provider",
            "calculation_mode",
            "payment_type",
            "zone",
            "is_active",
            "sort_order",
            "estimated_days",
            "min_order_amount",
            "free_shipping_threshold",
            "config",
        )

    def clean_config(self):
        value = self.cleaned_data.get("config")
        if value in (None, ""):
            return {}
        return value


class StoreShippingMethodInline(StackedInline):
    """Edit this store's shipping methods on the store change form."""

    model = ShippingMethod
    form = _ShippingMethodInlineForm
    extra = 0
    tab = True
    show_change_link = True
    autocomplete_fields = ("zone",)
    prepopulated_fields = {"slug": ("name",)}
    verbose_name = "روش ارسال"
    verbose_name_plural = "روش‌های ارسال"
    fields = (
        ("name", "slug"),
        ("provider", "calculation_mode", "payment_type"),
        "zone",
        ("is_active", "sort_order", "estimated_days"),
        ("min_order_amount", "free_shipping_threshold"),
        "config",
    )


@admin.register(Theme)
class ThemeAdmin(ModelAdmin):
    list_display = ("name", "slug", "directory", "is_active", "is_default", "created_at")
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "slug", "directory")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Store)
class StoreAdmin(ModelAdmin):
    form = StoreConfigForm
    compressed_fields = True
    warn_unsaved_form = True
    list_display = (
        "name",
        "slug",
        "store_manager_display",
        "store_type",
        "status",
        "theme",
        "currency",
        "tax_enabled",
        "created_at",
    )
    list_filter = ("store_type", "status", "tax_enabled")
    search_fields = ("name", "slug", "memberships__user__phone", "memberships__user__first_name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("theme", "default_theme")
    inlines = [DomainInline, StoreShippingMethodInline, StorePluginInline, StoreSettingInline]
    fieldsets = (
        (
            "اطلاعات پایه",
            {
                "classes": ["tab"],
                "description": "نام، شناسه، نوع و وضعیت فروشگاه.",
                "fields": (("name", "slug"), ("store_type", "status")),
            },
        ),
        (
            "دامنه و برندینگ",
            {
                "classes": ["tab"],
                "description": "تم فروشگاه، لوگو، رنگ‌ها و نشان‌های اعتماد. دامنه‌ها را از تب «دامنه‌ها» مدیریت کنید.",
                "fields": (
                    ("theme", "default_theme"),
                    "theme_logo",
                    ("theme_color_primary", "theme_color_background", "theme_color_text"),
                    ("trust_enamad_image", "trust_enamad_link"),
                    ("trust_badge2_image", "trust_badge2_link"),
                ),
            },
        ),
        (
            "تماس و شبکه‌های اجتماعی",
            {
                "classes": ["tab"],
                "description": "اطلاعات تماس و لینک شبکه‌های اجتماعی فروشگاه.",
                "fields": (
                    ("contact_phone", "contact_whatsapp"),
                    "contact_email",
                    "contact_address",
                    ("social_instagram", "social_telegram"),
                    ("social_twitter", "social_linkedin"),
                    "social_youtube",
                ),
            },
        ),
        (
            "فروش و مالی",
            {
                "classes": ["tab"],
                "description": (
                    "ارز، زبان، مالیات و درگاه‌های پرداخت. "
                    "با فعال‌کردن مالیات و درصد بیشتر از صفر (مثلاً ۹)، مبلغ مالیات در تسویه نشان داده می‌شود."
                ),
                "fields": (
                    ("currency", "timezone", "language"),
                    ("tax_enabled", "tax_percent", "tax_on_shipping"),
                    "payment_gateways",
                    "payment_default_gateway",
                    "payment_callback_base_url",
                    ("zarinpal_merchant_id", "zarinpal_sandbox"),
                    "zarinpal_api_base",
                    "zarinpal_start_pay_url",
                    "zarinpal_graphql_url",
                ),
            },
        ),
        (
            "ارسال",
            {
                "classes": ["tab"],
                "description": (
                    "مبدا، وزن بسته‌بندی و آستانه ارسال رایگان فروشگاه. "
                    "روش‌های ارسال این فروشگاه را از تب «روش‌های ارسال» همین صفحه ویرایش کنید. "
                    "تعرفه شهر/منطقه را با لینک ویرایش هر روش یا از منوی روش‌های ارسال تنظیم کنید."
                ),
                "fields": (
                    ("shipping_origin_province", "shipping_origin_city"),
                    "shipping_providers",
                    ("shipping_default_provider", "shipping_free_threshold"),
                    "shipping_base_package_weight_kg",
                ),
            },
        ),
        (
            "سئو و متا",
            {
                "classes": ["tab"],
                "description": "متادیتای پیش‌فرض سطح فروشگاه و اتصال به گوگل سرچ کنسول.",
                "fields": (
                    "seo_meta_title",
                    "seo_meta_description",
                    "seo_meta_keywords",
                    ("seo_og_image", "seo_canonical_url"),
                    "seo_robots",
                    "seo_google_site_verification",
                ),
            },
        ),
        (
            "چیدمان و سایر",
            {
                "classes": ["tab"],
                "description": (
                    "هدر/فوتر سفارشی و درایور ذخیره‌سازی. "
                    "درگاه‌های جانبی، اسنیپت ارسال و اسلایدر تم را در تب «پیشرفته (فرم)» ویرایش کنید؛ "
                    "تم کامل و کلیدهای سفارشی در تب «تنظیمات پیشرفته (JSON)» هستند. "
                    "قالب‌های آماده JSON در سایدبار «مستندات ← قالب‌های JSON»."
                ),
                "fields": (
                    ("layout_use_custom_header", "layout_use_custom_footer"),
                    "layout_header_html",
                    "layout_footer_html",
                    "storage_driver",
                ),
            },
        ),
        (
            "پیشرفته (فرم)",
            {
                "classes": ["tab"],
                "description": (
                    "درگاه‌های جانبی، اسنیپت‌های ارسال و اسلایدر تم با فرم یا JSON. "
                    "ویرایش فیلدها یا کادر JSON با ذخیره اعمال می‌شود. "
                    "تم کامل (theme/config) همچنان در تب JSON قابل ویرایش است. "
                    "کپی قالب‌های آماده: سایدبار «مستندات ← قالب‌های JSON»."
                ),
                "fields": (
                    ("idpay_api_key", "idpay_sandbox"),
                    "idpay_use_json",
                    "idpay_json",
                    ("mellat_terminal_id", "mellat_username"),
                    "mellat_password",
                    "mellat_sandbox",
                    "mellat_use_json",
                    "mellat_json",
                    ("pasargad_merchant_code", "pasargad_terminal_id"),
                    "pasargad_sandbox",
                    "pasargad_use_json",
                    "pasargad_json",
                    ("sina_terminal_id", "sina_sandbox"),
                    "sina_use_json",
                    "sina_json",
                    ("ship_post_fixed_price", "ship_post_max_weight_kg"),
                    "ship_post_use_json",
                    "ship_post_json",
                    "ship_tipax_fixed_price",
                    "ship_tipax_use_json",
                    "ship_tipax_json",
                    "ship_peyk_fixed_price",
                    "ship_peyk_delivery_cities",
                    "ship_peyk_use_json",
                    "ship_peyk_json",
                    "theme_hero_slides_json",
                    "theme_hero_use_json",
                ),
            },
        ),
        (
            "مدیر فروشگاه",
            {
                "classes": ["tab"],
                "description": "مدیر اصلی فروشگاه را ببینید یا عوض کنید. این شخص به پنل مدیریت فروشگاه دسترسی پیدا می‌کند.",
                "fields": (
                    "store_manager_phone",
                    ("store_manager_first_name", "store_manager_last_name"),
                ),
            },
        ),
    )
    MANAGER_FORM_FIELDS = (
        "store_manager_phone",
        "store_manager_first_name",
        "store_manager_last_name",
    )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        # On GET, ensure catalog rows exist so admins can edit known JSON without memorizing keys.
        # Never runs on POST and never overwrites existing values.
        if object_id and request.method == "GET":
            store = self.get_object(request, object_id)
            if store is not None:
                ensure_advanced_setting_rows(store)
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            Prefetch(
                "memberships",
                queryset=StoreMembership.objects.filter(is_primary=True).select_related("user"),
                to_attr="_primary_memberships",
            )
        )

    @admin.display(description="مدیر فروشگاه")
    def store_manager_display(self, obj):
        items = getattr(obj, "_primary_memberships", None)
        membership = items[0] if items else None
        if membership is None and items is None:
            membership = (
                StoreMembership.objects.filter(store=obj, is_primary=True)
                .select_related("user")
                .first()
            )
        if not membership:
            return "—"
        user = membership.user
        if user.full_name != user.phone:
            return f"{user.full_name} ({user.phone})"
        return user.phone

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets
        return tuple(fs for fs in fieldsets if fs[0] != "مدیر فروشگاه")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            for name in self.MANAGER_FORM_FIELDS:
                form.base_fields.pop(name, None)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # After inlines so form-owned keys win over any leftover JSON rows,
        # and theme hero slides can apply on top of theme.config from the JSON tab.
        super().save_related(request, form, formsets, change)
        if isinstance(form, StoreConfigForm):
            form.save_related_config()


@admin.register(Domain)
class DomainAdmin(ModelAdmin):
    list_display = ("domain", "store", "is_primary", "ssl_enabled", "is_active")
    list_filter = ("is_primary", "ssl_enabled", "is_active")
    search_fields = ("domain", "store__name")
    autocomplete_fields = ("store",)


@admin.register(StoreSetting)
class StoreSettingAdmin(ModelAdmin):
    form = _StoreSettingInlineForm
    list_display = ("store", "group", "key", "value_type", "updated_at")
    list_filter = ("group", "value_type", "store")
    search_fields = ("key", "store__name", "description")
    autocomplete_fields = ("store",)


@admin.register(Plugin)
class PluginAdmin(ModelAdmin):
    list_display = ("name", "codename", "is_active", "is_system", "created_at")
    list_filter = ("is_active", "is_system")
    search_fields = ("name", "codename")


@admin.register(StorePlugin)
class StorePluginAdmin(ModelAdmin):
    list_display = ("store", "plugin", "is_enabled", "updated_at")
    list_filter = ("is_enabled", "plugin", "store")
    search_fields = ("store__name", "plugin__codename")
    autocomplete_fields = ("store", "plugin")
