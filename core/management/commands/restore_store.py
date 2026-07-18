"""Restore a store from a backup archive."""

from django.core.management.base import BaseCommand

from core.services.backup import BackupError, RestoreService
from tenants.models import Store


class Command(BaseCommand):
    help = "Restore store data from a backup archive"

    def add_arguments(self, parser):
        parser.add_argument("--store", type=str, required=True, help="Store slug")
        parser.add_argument("--archive", type=str, required=True, help="Path to .shopcms-backup.zip")
        parser.add_argument("--dry-run", action="store_true", help="Validate only, do not restore")
        parser.add_argument("--yes", action="store_true", help="Skip interactive confirmation")

    def handle(self, *args, **options):
        store = Store.objects.get(slug=options["store"])
        if not options["yes"] and not options["dry_run"]:
            confirm = input(f"Restore will replace data for '{store.slug}'. Type slug to confirm: ")
            if confirm != store.slug:
                self.stderr.write(self.style.ERROR("Confirmation failed"))
                return

        service = RestoreService()
        try:
            result = service.restore_store_backup(
                store,
                options["archive"],
                dry_run=options["dry_run"],
                confirm_slug=store.slug,
            )
        except BackupError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        if result["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"Dry run OK. Records: {result['record_count']}"))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Restored {result['restored_records']} records and {result['media_files']} media files"
                )
            )
