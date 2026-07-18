"""Create a store backup archive."""

from django.core.management.base import BaseCommand

from core.services.backup import BackupError, BackupService
from tenants.models import Store


class Command(BaseCommand):
    help = "Create a backup archive for a store"

    def add_arguments(self, parser):
        parser.add_argument("--store", type=str, required=True, help="Store slug")
        parser.add_argument("--no-media", action="store_true", help="Exclude media files")

    def handle(self, *args, **options):
        store = Store.objects.get(slug=options["store"])
        service = BackupService()
        try:
            job = service.create_store_backup(store, include_media=not options["no_media"])
        except BackupError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return
        self.stdout.write(
            self.style.SUCCESS(
                f"Backup completed: {job.file_path} ({job.record_count} records, {job.file_size} bytes)"
            )
        )
