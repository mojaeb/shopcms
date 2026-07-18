"""Super admin platform backup API."""

from pathlib import Path

from django.http import FileResponse
from ninja import Router
from ninja.errors import HttpError

from core.api.backup import BackupJobSchema, _job_schema
from core.enums import BackupScope
from core.models import BackupJob
from core.services.backup import BackupError, BackupService
from dashboard.authentication import super_admin_auth

router = Router(auth=super_admin_auth)
backup_service = BackupService()


@router.get("/", response=list[BackupJobSchema])
def list_platform_backups(request):
    jobs = backup_service.list_backups(scope=BackupScope.PLATFORM)
    return [_job_schema(job) for job in jobs]


@router.post("/", response=BackupJobSchema)
def create_platform_backup(request):
    try:
        job = backup_service.create_platform_backup()
    except BackupError as exc:
        raise HttpError(400, str(exc)) from exc
    return _job_schema(job)


@router.get("/{job_id}/download")
def download_platform_backup(request, job_id: int):
    job = BackupJob.objects.filter(id=job_id, scope=BackupScope.PLATFORM).first()
    if not job or not job.file_path:
        raise HttpError(404, "بکاپ یافت نشد")
    path = Path(job.file_path)
    if not path.exists():
        raise HttpError(404, "فایل بکاپ موجود نیست")
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)
