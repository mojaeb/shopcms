"""Tenant admin configuration."""

from django.contrib import admin

from tenants.models import Domain, Plugin, Store, StorePlugin, StoreSetting, Theme


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 1
    fields = ("domain", "is_primary", "ssl_enabled", "redirect_to_primary", "is_active")


class StoreSettingInline(admin.TabularInline):
    model = StoreSetting
    extra = 0
    fields = ("group", "key", "value", "value_type", "description")


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "directory", "is_active", "is_default", "created_at")
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "slug", "directory")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "store_type",
        "status",
        "theme",
        "currency",
        "tax_enabled",
        "created_at",
    )
    list_filter = ("store_type", "status", "tax_enabled")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [DomainInline, StoreSettingInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "store_type", "status")}),
        ("تم", {"fields": ("theme", "default_theme")}),
        ("تنظیمات منطقه‌ای", {"fields": ("currency", "timezone", "language")}),
        ("مالیات", {"fields": ("tax_enabled", "tax_percent")}),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "store", "is_primary", "ssl_enabled", "is_active")
    list_filter = ("is_primary", "ssl_enabled", "is_active")
    search_fields = ("domain", "store__name")


@admin.register(StoreSetting)
class StoreSettingAdmin(admin.ModelAdmin):
    list_display = ("store", "group", "key", "value_type", "updated_at")
    list_filter = ("group", "value_type", "store")
    search_fields = ("key", "store__name")


@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = ("name", "codename", "is_active", "is_system", "created_at")
    list_filter = ("is_active", "is_system")
    search_fields = ("name", "codename")


@admin.register(StorePlugin)
class StorePluginAdmin(admin.ModelAdmin):
    list_display = ("store", "plugin", "is_enabled", "updated_at")
    list_filter = ("is_enabled", "plugin", "store")
    search_fields = ("store__name", "plugin__codename")
