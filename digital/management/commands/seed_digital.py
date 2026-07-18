"""Seed digital download demo data."""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from PIL import Image

from digital.services.digital import DigitalService
from files.services.file import FileService
from plugins.services.plugin import PluginService
from products.enums import ProductStatus, ProductType
from products.models import Product
from tenants.enums import StoreType
from tenants.models import Domain, Store, Theme


class Command(BaseCommand):
    help = "Seed digital product with downloadable file"

    def handle(self, *args, **options):
        theme, _ = Theme.objects.get_or_create(
            slug="default",
            defaults={"name": "Default", "directory": "default", "is_default": True},
        )
        store, _ = Store.objects.get_or_create(
            slug="digital-shop",
            defaults={
                "name": "Digital Shop",
                "default_theme": theme,
                "status": "active",
                "store_type": StoreType.DIGITAL_DOWNLOAD,
            },
        )
        Domain.objects.get_or_create(store=store, domain="digital.local", defaults={"is_primary": True})

        PluginService().sync_registry_to_db()
        PluginService().install_defaults(store)

        product, _ = Product.objects.get_or_create(
            store=store,
            slug="ebook-sample",
            defaults={
                "name": "نمونه کتاب الکترونیک",
                "description": "فایل PDF نمونه",
                "product_type": ProductType.DIGITAL,
                "status": ProductStatus.ACTIVE,
                "base_price": 50000,
            },
        )

        if product.digital_assets.exists():
            self.stdout.write("Digital demo already exists.")
            return

        buffer = BytesIO()
        Image.new("RGB", (400, 300), color=(40, 80, 120)).save(buffer, format="JPEG")
        buffer.seek(0)
        uploaded = SimpleUploadedFile("ebook-cover.jpg", buffer.read(), content_type="image/jpeg")
        media = FileService().upload(store, uploaded, folder="digital", title="Ebook File")

        DigitalService().attach_asset(
            store, product.id, media.id, title="فایل کتاب", max_downloads=3, expire_hours=48,
        )
        self.stdout.write(self.style.SUCCESS(f"Digital product seeded: {product.slug}"))
