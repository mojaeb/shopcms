"""Digital downloads admin."""

from django.contrib import admin

from digital.models import DownloadLicense, ProductDigitalAsset


@admin.register(ProductDigitalAsset)
class ProductDigitalAssetAdmin(admin.ModelAdmin):
    list_display = ("product", "media_file", "store", "max_downloads", "expire_hours")
    list_filter = ("store",)


@admin.register(DownloadLicense)
class DownloadLicenseAdmin(admin.ModelAdmin):
    list_display = ("user", "media_file", "order", "status", "download_count", "max_downloads", "expires_at")
    list_filter = ("store", "status")
    search_fields = ("token", "user__phone")
