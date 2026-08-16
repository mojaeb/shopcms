"""Files admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from files.models import FileThumbnail, MediaFile


class FileThumbnailInline(TabularInline):
    model = FileThumbnail
    extra = 0
    readonly_fields = ("variant", "url", "width", "height", "size_bytes")


@admin.register(MediaFile)
class MediaFileAdmin(ModelAdmin):
    list_display = ("original_name", "store", "file_type", "size_bytes", "storage_driver", "created_at")
    list_filter = ("store", "file_type", "storage_driver")
    search_fields = ("original_name", "title")
    inlines = [FileThumbnailInline]


@admin.register(FileThumbnail)
class FileThumbnailAdmin(ModelAdmin):
    list_display = ("media_file", "variant", "width", "height", "size_bytes")
