"""Tenant admin configuration — unified store settings form (Unfold)."""

from django import forms
from django.contrib import admin
from django.db.models import Prefetch, Q
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from accounts.models import StoreMembership
from tenants.forms import StoreConfigForm
from tenants.models import Domain, Plugin, Store, StorePlugin, StoreSetting, Theme
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


class _StoreSettingInlineForm(forms.ModelForm):
    """Allow empty JSON string values; coerce blank submissions to empty string."""

    class Meta:
        model = StoreSetting
        fields = ("group", "key", "value", "value_type", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        value_field = self.fields["value"]
        value_field.required = False
        # Keep pretty multi-line JSON in the Unfold textarea.
        if hasattr(value_field, "widget"):
            value_field.widget.attrs.setdefault("dir", "ltr")

    def clean_value(self):
        value = self.cleaned_data.get("value")
        if value is None:
            return ""
        return value


class StoreSettingInline(StackedInline):
    """Raw key/value settings for advanced / unknown keys (hero slides, gateway extras, …)."""

    model = StoreSetting
    form = _StoreSettingInlineForm
    extra = 0
    tab = True
    collapsible = True
    verbose_name = "تنظیم پیشرفته"
    verbose_name_plural = "تنظیمات پیشرفته (JSON)"
    fields = ("group", "key", "value", "value_type", "description")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        exclude = Q()
        for group, key in STRUCTURED_ADMIN_SETTING_KEYS:
            exclude |= Q(group=group, key=key)
        return qs.exclude(exclude) if STRUCTURED_ADMIN_SETTING_KEYS else qs


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
    inlines = [DomainInline, StorePluginInline, StoreSettingInline]
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
                "description": "ارز، زبان، مالیات و درگاه‌های پرداخت.",
                "fields": (
                    ("currency", "timezone", "language"),
                    ("tax_enabled", "tax_percent", "tax_on_shipping"),
                    "payment_gateways",
                    "payment_default_gateway",
                    ("zarinpal_merchant_id", "zarinpal_sandbox"),
                ),
            },
        ),
        (
            "ارسال",
            {
                "classes": ["tab"],
                "description": "مبدا ارسال و آستانه ارسال رایگان. روش‌های ارسال جزئی در بخش «ارسال» تعریف می‌شوند.",
                "fields": (
                    ("shipping_origin_province", "shipping_origin_city"),
                    ("shipping_free_threshold", "shipping_default_provider"),
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
                "description": "هدر/فوتر سفارشی و درایور ذخیره‌سازی. مقادیر JSON پیشرفته در تب «تنظیمات پیشرفته» هستند.",
                "fields": (
                    ("layout_use_custom_header", "layout_use_custom_footer"),
                    "layout_header_html",
                    "layout_footer_html",
                    "storage_driver",
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
