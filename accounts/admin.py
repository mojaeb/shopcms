"""Account admin configuration."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import OTPCode, Permission, Role, StoreMembership, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("phone", "full_name", "email", "is_active", "is_staff", "phone_verified", "created_at")
    list_filter = ("is_active", "is_staff", "is_superuser", "phone_verified")
    search_fields = ("phone", "email", "first_name", "last_name")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "email")}),
        ("دسترسی‌ها", {"fields": ("is_active", "is_staff", "is_superuser", "phone_verified", "groups", "user_permissions")}),
        ("متادیتا", {"fields": ("last_login", "last_login_ip")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("phone", "password1", "password2", "is_staff", "is_superuser")}),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "codename", "scope", "is_system", "created_at")
    list_filter = ("scope", "is_system")
    search_fields = ("name", "codename")
    filter_horizontal = ("permissions",)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "name", "group")
    list_filter = ("group",)
    search_fields = ("codename", "name")


@admin.register(StoreMembership)
class StoreMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "store", "role", "status", "is_primary", "created_at")
    list_filter = ("status", "role", "store", "is_primary")
    search_fields = ("user__phone", "store__name")
    raw_id_fields = ("user", "store")


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("phone", "purpose", "code", "is_used", "expires_at", "attempts", "created_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("phone",)
    readonly_fields = ("code", "created_at", "updated_at")
