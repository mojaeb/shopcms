"""Export current DB + media into docker/seed-data for staging deploy."""

from __future__ import annotations

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Export DB fixtures + media into docker/seed-data for Docker staging"

    def add_arguments(self, parser):
        parser.add_argument(
            "--out",
            default=str(settings.BASE_DIR / "docker" / "seed-data"),
            help="Output directory (default: docker/seed-data)",
        )

    def handle(self, *args, **options):
        out = Path(options["out"]).resolve()
        out.mkdir(parents=True, exist_ok=True)
        media_out = out / "media"
        data_path = out / "data.json"

        self.stdout.write(f"Exporting fixtures -> {data_path}")
        with data_path.open("w", encoding="utf-8") as fh:
            call_command(
                "dumpdata",
                "--natural-foreign",
                "--natural-primary",
                "--indent",
                "2",
                exclude=[
                    "sessions.session",
                    "admin.logentry",
                ],
                stdout=fh,
            )

        media_root = Path(settings.MEDIA_ROOT)
        if media_out.exists():
            shutil.rmtree(media_out)
        if media_root.exists():
            self.stdout.write(f"Copying media -> {media_out}")
            shutil.copytree(media_root, media_out)
        else:
            media_out.mkdir(parents=True, exist_ok=True)
            self.stdout.write(self.style.WARNING("MEDIA_ROOT missing - empty media exported"))

        size_mb = data_path.stat().st_size / (1024 * 1024)
        media_files = sum(1 for p in media_out.rglob("*") if p.is_file())
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. data.json={size_mb:.2f} MB, media_files={media_files}, out={out}"
            )
        )
        self.stdout.write(
            "Deploy with: docker compose -f docker/docker-compose.staging.yml --env-file .env.staging up --build -d"
        )
