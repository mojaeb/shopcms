"""Digital download service."""

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from digital.enums import LicenseStatus
from digital.models import DownloadLicense, ProductDigitalAsset, generate_download_token
from files.models import MediaFile
from orders.models import Order
from plugins.services.plugin import PluginService
from products.models import Product

logger = logging.getLogger(__name__)

DEFAULT_MAX_DOWNLOADS = 5
DEFAULT_EXPIRE_HOURS = 72


class DigitalError(Exception):
    pass


class DigitalService:
    """Manage digital assets and download licenses."""

    PLUGIN_CODENAME = "digital_download"

    def is_active(self, store) -> bool:
        return PluginService().is_enabled(store, self.PLUGIN_CODENAME)

    def get_plugin_settings(self, store) -> dict:
        settings = PluginService().get_settings(store, self.PLUGIN_CODENAME)
        return {
            "max_downloads": int(settings.get("max_downloads", DEFAULT_MAX_DOWNLOADS)),
            "link_expire_hours": int(settings.get("link_expire_hours", DEFAULT_EXPIRE_HOURS)),
        }

    def list_product_assets(self, store, product_id: int):
        return ProductDigitalAsset.objects.filter(store=store, product_id=product_id).select_related("media_file")

    def attach_asset(
        self,
        store,
        product_id: int,
        media_file_id: int,
        title: str = "",
        max_downloads: int | None = None,
        expire_hours: int | None = None,
    ) -> ProductDigitalAsset:
        product = Product.objects.get(pk=product_id, store=store)
        media = MediaFile.objects.get(pk=media_file_id, store=store)
        asset, _ = ProductDigitalAsset.objects.update_or_create(
            product=product,
            media_file=media,
            defaults={
                "store": store,
                "title": title or media.title or media.original_name,
                "max_downloads": max_downloads,
                "expire_hours": expire_hours,
            },
        )
        if product.product_type != "digital":
            product.product_type = "digital"
            product.save(update_fields=["product_type", "updated_at"])
        return asset

    def detach_asset(self, store, product_id: int, asset_id: int) -> None:
        ProductDigitalAsset.objects.filter(store=store, product_id=product_id, pk=asset_id).delete()

    @transaction.atomic
    def issue_licenses_for_order(self, order: Order) -> list[DownloadLicense]:
        if not self.is_active(order.store):
            return []

        plugin_settings = self.get_plugin_settings(order.store)
        created = []

        for item in order.items.all():
            assets = ProductDigitalAsset.objects.filter(
                store=order.store,
                product_id=item.product_id,
            ).select_related("media_file")

            for asset in assets:
                max_downloads = asset.max_downloads or plugin_settings["max_downloads"]
                max_downloads *= max(1, item.quantity)

                expire_hours = asset.expire_hours or plugin_settings["link_expire_hours"]
                expires_at = timezone.now() + timedelta(hours=expire_hours) if expire_hours else None

                license_obj = DownloadLicense.objects.create(
                    store=order.store,
                    user=order.user,
                    order=order,
                    order_item=item,
                    product_id=item.product_id,
                    media_file=asset.media_file,
                    token=generate_download_token(),
                    max_downloads=max_downloads,
                    expires_at=expires_at,
                )
                created.append(license_obj)

        if created:
            logger.info("Issued %s download licenses for order %s", len(created), order.order_number)
        return created

    def list_user_licenses(self, user, store):
        self.refresh_license_statuses(user, store)
        return (
            DownloadLicense.objects.filter(store=store, user=user)
            .select_related("media_file", "order")
            .order_by("-created_at")
        )

    def refresh_license_statuses(self, user, store) -> None:
        now = timezone.now()
        qs = DownloadLicense.objects.filter(store=store, user=user, status=LicenseStatus.ACTIVE)
        for lic in qs:
            if lic.expires_at and lic.expires_at <= now:
                lic.status = LicenseStatus.EXPIRED
                lic.save(update_fields=["status", "updated_at"])
            elif lic.download_count >= lic.max_downloads:
                lic.status = LicenseStatus.EXHAUSTED
                lic.save(update_fields=["status", "updated_at"])

    def get_license_by_token(self, token: str) -> DownloadLicense:
        try:
            return DownloadLicense.objects.select_related("media_file", "user", "store").get(token=token)
        except DownloadLicense.DoesNotExist as exc:
            raise DigitalError("مجوز دانلود یافت نشد") from exc

    def validate_download(self, token: str, user=None) -> DownloadLicense:
        license_obj = self.get_license_by_token(token)
        self._refresh_single(license_obj)

        if user and license_obj.user_id != user.id:
            raise DigitalError("دسترسی مجاز نیست")

        if license_obj.status == LicenseStatus.REVOKED:
            raise DigitalError("مجوز دانلود لغو شده است")
        if license_obj.status == LicenseStatus.EXPIRED:
            raise DigitalError("مجوز دانلود منقضی شده است")
        if license_obj.status == LicenseStatus.EXHAUSTED:
            raise DigitalError("تعداد مجاز دانلود تمام شده است")

        return license_obj

    @transaction.atomic
    def record_download(self, license_obj: DownloadLicense) -> DownloadLicense:
        self._refresh_single(license_obj)
        if license_obj.status != LicenseStatus.ACTIVE:
            raise DigitalError("مجوز دانلود قابل استفاده نیست")

        license_obj.download_count += 1
        license_obj.last_download_at = timezone.now()
        if license_obj.download_count >= license_obj.max_downloads:
            license_obj.status = LicenseStatus.EXHAUSTED
        license_obj.save(update_fields=["download_count", "last_download_at", "status", "updated_at"])
        return license_obj

    @transaction.atomic
    def revoke_license(self, store, license_id: int) -> DownloadLicense:
        try:
            lic = DownloadLicense.objects.get(pk=license_id, store=store)
        except DownloadLicense.DoesNotExist as exc:
            raise DigitalError("مجوز یافت نشد") from exc
        lic.status = LicenseStatus.REVOKED
        lic.save(update_fields=["status", "updated_at"])
        return lic

    def serialize_license(self, lic: DownloadLicense) -> dict:
        remaining = max(0, lic.max_downloads - lic.download_count)
        return {
            "id": lic.id,
            "token": lic.token,
            "product_id": lic.product_id,
            "product_name": lic.order_item.product_name,
            "file_name": lic.media_file.original_name,
            "file_title": lic.media_file.title or lic.media_file.original_name,
            "order_number": lic.order.order_number,
            "max_downloads": lic.max_downloads,
            "download_count": lic.download_count,
            "downloads_remaining": remaining,
            "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
            "status": lic.status,
            "status_label": lic.get_status_display(),
            "last_download_at": lic.last_download_at.isoformat() if lic.last_download_at else None,
            "download_url": f"/download/{lic.token}/",
            "created_at": lic.created_at.isoformat(),
        }

    def serialize_asset(self, asset: ProductDigitalAsset) -> dict:
        media = asset.media_file
        return {
            "id": asset.id,
            "product_id": asset.product_id,
            "media_file_id": media.id,
            "title": asset.title,
            "file_name": media.original_name,
            "mime_type": media.mime_type,
            "size_bytes": media.size_bytes,
            "max_downloads": asset.max_downloads,
            "expire_hours": asset.expire_hours,
            "sort_order": asset.sort_order,
        }

    def _refresh_single(self, lic: DownloadLicense) -> None:
        if lic.status != LicenseStatus.ACTIVE:
            return
        now = timezone.now()
        if lic.expires_at and lic.expires_at <= now:
            lic.status = LicenseStatus.EXPIRED
            lic.save(update_fields=["status", "updated_at"])
        elif lic.download_count >= lic.max_downloads:
            lic.status = LicenseStatus.EXHAUSTED
            lic.save(update_fields=["status", "updated_at"])
