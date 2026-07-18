"""Store and platform backup/restore services."""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import zipfile
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core import serializers
from django.db import connection, transaction
from django.utils import timezone

from core.enums import BackupScope, BackupStatus
from core.models import BackupJob
from core.services.backup_manifest import MANIFEST_VERSION, store_export_specs
from tenants.models import Store
from tenants.services.cache import StoreCacheService

logger = logging.getLogger(__name__)


class BackupError(Exception):
    pass


class BackupService:
    """Create and manage backup archives."""

    def __init__(self):
        self.backup_root = Path(getattr(settings, "BACKUP_ROOT", settings.BASE_DIR / "backups"))
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def list_backups(self, store: Store | None = None, scope: str | None = None) -> list[BackupJob]:
        qs = BackupJob.objects.select_related("store").order_by("-created_at")
        if store:
            qs = qs.filter(store=store)
        if scope:
            qs = qs.filter(scope=scope)
        return list(qs)

    def create_store_backup(self, store: Store, include_media: bool = True) -> BackupJob:
        job = BackupJob.objects.create(
            store=store,
            scope=BackupScope.STORE,
            status=BackupStatus.RUNNING,
            include_media=include_media,
        )
        try:
            archive_path = self._store_archive_path(store, job.id)
            record_count, checksum = self._build_store_archive(store, archive_path, include_media=include_media)
            job.status = BackupStatus.COMPLETED
            job.file_path = str(archive_path)
            job.file_size = archive_path.stat().st_size
            job.record_count = record_count
            job.checksum = checksum
            job.completed_at = timezone.now()
            job.save()
            return job
        except Exception as exc:
            logger.exception("Store backup failed for %s", store.slug)
            job.status = BackupStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save()
            raise BackupError(str(exc)) from exc

    def create_platform_backup(self) -> BackupJob:
        job = BackupJob.objects.create(
            scope=BackupScope.PLATFORM,
            status=BackupStatus.RUNNING,
            include_media=True,
        )
        try:
            archive_path = self.backup_root / "platform" / f"platform-{timezone.now():%Y%m%d%H%M%S}.zip"
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            checksum = self._build_platform_archive(archive_path)
            job.status = BackupStatus.COMPLETED
            job.file_path = str(archive_path)
            job.file_size = archive_path.stat().st_size
            job.checksum = checksum
            job.completed_at = timezone.now()
            job.save()
            return job
        except Exception as exc:
            logger.exception("Platform backup failed")
            job.status = BackupStatus.FAILED
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save()
            raise BackupError(str(exc)) from exc

    def cleanup_old_backups(self, retention_days: int | None = None) -> dict:
        days = retention_days or getattr(settings, "BACKUP_RETENTION_DAYS", 30)
        cutoff = timezone.now() - timedelta(days=days)
        removed = 0
        for job in BackupJob.objects.filter(created_at__lt=cutoff, status=BackupStatus.COMPLETED):
            if job.file_path:
                Path(job.file_path).unlink(missing_ok=True)
            job.delete()
            removed += 1
        return {"removed": removed, "retention_days": days}

    def _store_archive_path(self, store: Store, job_id: int) -> Path:
        folder = self.backup_root / "stores" / store.slug
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{store.slug}-{job_id}-{timezone.now():%Y%m%d%H%M%S}.shopcms-backup.zip"

    def _export_store_records(self, store: Store) -> tuple[list[dict], int]:
        records: list[dict] = []
        total = 0
        for label, queryset_fn in store_export_specs():
            queryset = queryset_fn(store)
            if not queryset.exists():
                continue
            chunk = serializers.serialize("python", queryset)
            records.extend(chunk)
            total += len(chunk)
        return records, total

    def _build_store_archive(self, store: Store, archive_path: Path, include_media: bool) -> tuple[int, str]:
        records, record_count = self._export_store_records(store)
        manifest = {
            "version": MANIFEST_VERSION,
            "scope": BackupScope.STORE,
            "store_id": store.id,
            "store_slug": store.slug,
            "store_name": store.name,
            "created_at": timezone.now().isoformat(),
            "django_version": getattr(settings, "PLATFORM_VERSION", "0.1.0"),
            "include_media": include_media,
            "record_count": record_count,
        }
        data_bytes = json.dumps(records, ensure_ascii=False, default=str).encode("utf-8")
        checksum = hashlib.sha256(data_bytes).hexdigest()
        manifest["checksum"] = checksum

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            zf.writestr("data.json", data_bytes)
            if include_media:
                media_dir = Path(settings.MEDIA_ROOT) / "stores" / store.slug
                if media_dir.exists():
                    for path in media_dir.rglob("*"):
                        if path.is_file():
                            zf.write(path, arcname=f"media/{path.relative_to(settings.MEDIA_ROOT).as_posix()}")
        return record_count, checksum

    def _build_platform_archive(self, archive_path: Path) -> str:
        manifest = {
            "version": MANIFEST_VERSION,
            "scope": BackupScope.PLATFORM,
            "created_at": timezone.now().isoformat(),
            "database_engine": connection.settings_dict["ENGINE"],
        }
        hasher = hashlib.sha256()

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

            engine = connection.settings_dict["ENGINE"]
            if "sqlite" in engine:
                db_path = Path(connection.settings_dict["NAME"])
                if db_path.exists():
                    zf.write(db_path, arcname="database/db.sqlite3")
                    hasher.update(db_path.read_bytes())
            elif "postgresql" in engine:
                dump_path = archive_path.parent / "dump.sql"
                self._run_pg_dump(dump_path)
                zf.write(dump_path, arcname="database/dump.sql")
                hasher.update(dump_path.read_bytes())
                dump_path.unlink(missing_ok=True)

            media_root = Path(settings.MEDIA_ROOT)
            if media_root.exists():
                for path in media_root.rglob("*"):
                    if path.is_file():
                        zf.write(path, arcname=f"media/{path.relative_to(media_root).as_posix()}")

        return hasher.hexdigest()

    def _run_pg_dump(self, output_path: Path) -> None:
        db = connection.settings_dict
        command = [
            "pg_dump",
            "--dbname",
            db["NAME"],
            "--host",
            str(db.get("HOST") or "localhost"),
            "--port",
            str(db.get("PORT") or "5432"),
            "--username",
            str(db.get("USER") or ""),
            "--file",
            str(output_path),
            "--format",
            "plain",
            "--no-owner",
        ]
        env = None
        if db.get("PASSWORD"):
            env = {**os.environ, "PGPASSWORD": str(db["PASSWORD"])}
        result = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
        if result.returncode != 0:
            raise BackupError(result.stderr or "pg_dump failed")


class RestoreService:
    """Restore store data from backup archives."""

    def __init__(self):
        self.cache_service = StoreCacheService()

    def restore_store_backup(
        self,
        store: Store,
        archive_path: str | Path,
        *,
        dry_run: bool = False,
        confirm_slug: str | None = None,
    ) -> dict:
        archive_path = Path(archive_path)
        if not archive_path.exists():
            raise BackupError("فایل بکاپ یافت نشد")

        with zipfile.ZipFile(archive_path, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            data_bytes = zf.read("data.json")
            records = json.loads(data_bytes)

        checksum = hashlib.sha256(data_bytes).hexdigest()
        if manifest.get("scope") != BackupScope.STORE:
            raise BackupError("این بکاپ مربوط به فروشگاه نیست")
        if manifest.get("store_slug") != store.slug:
            raise BackupError("بکاپ با فروشگاه هدف مطابقت ندارد")
        if confirm_slug and confirm_slug != store.slug:
            raise BackupError("تایید slug فروشگاه نامعتبر است")
        if manifest.get("checksum") and manifest["checksum"] != checksum:
            raise BackupError("checksum بکاپ نامعتبر است")

        summary = {
            "dry_run": dry_run,
            "record_count": len(records),
            "store_slug": store.slug,
            "include_media": manifest.get("include_media", False),
            "restored_records": 0,
            "media_files": 0,
        }

        if dry_run:
            return summary

        with transaction.atomic():
            self._clear_store_data(store)
            restored = self._import_records(records)
            summary["restored_records"] = restored
            if manifest.get("include_media"):
                summary["media_files"] = self._restore_media(archive_path, store)

        self.cache_service.invalidate_store(store)
        return summary

    def _read_store_archive(self, archive_path: Path) -> tuple[dict, list[dict]]:
        with zipfile.ZipFile(archive_path, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            records = json.loads(zf.read("data.json"))
        return manifest, records

    def _clear_store_data(self, store: Store) -> None:
        for label, queryset_fn in reversed(store_export_specs()):
            queryset_fn(store).delete()

    def _import_records(self, records: list[dict]) -> int:
        restored = 0
        for item in serializers.deserialize("python", records, ignorenonexistent=True):
            item.save()
            restored += 1
        return restored

    def _restore_media(self, archive_path: Path, store: Store) -> int:
        restored = 0
        media_root = Path(settings.MEDIA_ROOT)
        prefix = f"media/stores/{store.slug}/"
        with zipfile.ZipFile(archive_path, "r") as zf:
            for name in zf.namelist():
                if not name.startswith(prefix):
                    continue
                target = media_root / Path(name).relative_to("media")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(name))
                restored += 1
        return restored
