"""Notifications admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from notifications.models import NotificationChannel, NotificationLog


@admin.register(NotificationChannel)
class NotificationChannelAdmin(ModelAdmin):
    list_display = ("store", "channel_type", "provider", "is_default", "is_active")
    list_filter = ("store", "channel_type", "provider", "is_active")
    search_fields = ("provider", "store__name")
    autocomplete_fields = ("store",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "store",
                    ("channel_type", "provider"),
                    ("is_default", "is_active"),
                    "config",
                ),
                "description": (
                    "برای ملی‌پیامک provider را payamak بگذارید و در config این کلیدها را پر کنید: "
                    "username، password، body_id (پترن OTP)، otp_template."
                ),
            },
        ),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ("channel_type", "provider", "recipient", "status", "created_at")
    list_filter = ("store", "channel_type", "status")
    search_fields = ("recipient", "body")
