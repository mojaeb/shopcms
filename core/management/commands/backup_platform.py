"""Create a full platform backup archive."""

from django.core.management.base import BaseCommand

from core.services.backup import BackupError, BackupService


class Command(BaseCommand):
    help = "Create a platform-wide backup (database + media)"

    def handle(self, *args, **options):
        service = BackupService()
        try:
            job = service.create_platform_backup()
        except BackupError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return
        self.stdout.write(
            self.style.SUCCESS(f"Platform backup completed: {job.file_path} ({job.file_size} bytes)")
        )
