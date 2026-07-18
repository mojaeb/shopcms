"""Seed sample media files."""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from PIL import Image

from files.services.file import FileService
from tenants.models import Domain, Store, Theme


class Command(BaseCommand):
    help = "Seed sample media files for demo store"

    def handle(self, *args, **options):
        theme, _ = Theme.objects.get_or_create(
            slug="default",
            defaults={"name": "Default", "directory": "default", "is_default": True},
        )
        store, _ = Store.objects.get_or_create(
            slug="shop1",
            defaults={"name": "Demo Shop", "default_theme": theme, "status": "active"},
        )
        Domain.objects.get_or_create(store=store, domain="shop1.local", defaults={"is_primary": True})

        service = FileService()
        if service.list_files(store, file_type="image").exists():
            self.stdout.write("Sample media already exists, skipping.")
            return

        buffer = BytesIO()
        image = Image.new("RGB", (800, 600), color=(52, 120, 180))
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        uploaded = SimpleUploadedFile(
            "sample-banner.jpg",
            buffer.read(),
            content_type="image/jpeg",
        )
        media = service.upload(store, uploaded, folder="banners", title="Sample Banner")
        self.stdout.write(self.style.SUCCESS(f"Created media file: {media.url}"))
        self.stdout.write(self.style.SUCCESS("Media files seeded successfully."))
