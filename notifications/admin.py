"""Notifications admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from notifications.models import NotificationChannel, NotificationLog


@admin.register(NotificationChannel)
class NotificationChannelAdmin(ModelAdmin):
    list_display = ("store", "channel_type", "provider", "is_default", "is_active")
    list_filter = ("store", "channel_type", "is_active")


@admin.register(NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ("channel_type", "provider", "recipient", "status", "created_at")
    list_filter = ("store", "channel_type", "status")
    search_fields = ("recipient", "body")
