"""Store admin backup API."""

from pathlib import Path

from django.http import FileResponse
from ninja import Router, Schema
from ninja.errors import HttpError

from core.enums import BackupScope
from core.models import BackupJob
from core.services.backup import BackupError, BackupService, RestoreService
from dashboard.authentication_store import store_backup_auth
from tenants.context import get_current_store

router = Router(auth=store_backup_auth)
backup_service = BackupService()
restore_service = RestoreService()


class BackupCreateSchema(Schema):
    include_media: bool = True


class BackupRestoreSchema(Schema):
    confirm_slug: str
    dry_run: bool = False


class BackupJobSchema(Schema):
    id: int
    status: str
    scope: str
    file_size: int
    record_count: int
    include_media: bool
    checksum: str
    error_message: str
    created_at: str
    completed_at: str | None


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


def _job_schema(job: BackupJob) -> BackupJobSchema:
    return BackupJobSchema(
        id=job.id,
        status=job.status,
        scope=job.scope,
        file_size=job.file_size,
        record_count=job.record_count,
        include_media=job.include_media,
        checksum=job.checksum,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.get("/", response=list[BackupJobSchema])
def list_backups(request):
    store = _store(request)
    jobs = backup_service.list_backups(store=store, scope=BackupScope.STORE)
    return [_job_schema(job) for job in jobs]


@router.post("/", response=BackupJobSchema)
def create_backup(request, payload: BackupCreateSchema):
    store = _store(request)
    try:
        job = backup_service.create_store_backup(store, include_media=payload.include_media)
    except BackupError as exc:
        raise HttpError(400, str(exc)) from exc
    return _job_schema(job)


@router.get("/{job_id}", response=BackupJobSchema)
def get_backup(request, job_id: int):
    store = _store(request)
    job = BackupJob.objects.filter(id=job_id, store=store, scope=BackupScope.STORE).first()
    if not job:
        raise HttpError(404, "بکاپ یافت نشد")
    return _job_schema(job)


@router.get("/{job_id}/download")
def download_backup(request, job_id: int):
    store = _store(request)
    job = BackupJob.objects.filter(id=job_id, store=store, scope=BackupScope.STORE).first()
    if not job or not job.file_path:
        raise HttpError(404, "بکاپ یافت نشد")
    path = Path(job.file_path)
    if not path.exists():
        raise HttpError(404, "فایل بکاپ موجود نیست")
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)


@router.post("/{job_id}/restore")
def restore_backup(request, job_id: int, payload: BackupRestoreSchema):
    store = _store(request)
    job = BackupJob.objects.filter(id=job_id, store=store, scope=BackupScope.STORE).first()
    if not job or not job.file_path:
        raise HttpError(404, "بکاپ یافت نشد")
    try:
        result = restore_service.restore_store_backup(
            store,
            job.file_path,
            dry_run=payload.dry_run,
            confirm_slug=payload.confirm_slug,
        )
    except BackupError as exc:
        raise HttpError(400, str(exc)) from exc
    return {"status": "ok", **result}
