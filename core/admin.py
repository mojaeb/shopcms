"""Core admin configuration."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from core.models import AuditLog, BackupJob


@admin.register(BackupJob)
class BackupJobAdmin(ModelAdmin):
    list_display = ("id", "store", "scope", "status", "file_size", "created_at")
    list_filter = ("scope", "status")
    readonly_fields = ("created_at", "updated_at", "completed_at")


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ("id", "action", "outcome", "user", "store", "ip_address", "created_at")
    list_filter = ("action", "outcome")
    readonly_fields = ("created_at", "updated_at")
