"""Secure file download view."""

from django.core.files.storage import default_storage
from django.http import FileResponse, Http404

from accounts.models import User
from accounts.services.jwt import JWTService
from digital.services.digital import DigitalError, DigitalService


def download_file(request, token: str):
    service = DigitalService()
    user = _optional_user(request)

    try:
        license_obj = service.validate_download(token)
    except DigitalError as exc:
        raise Http404(str(exc))

    if user and license_obj.user_id != user.id:
        raise Http404("دسترسی مجاز نیست")

    media = license_obj.media_file
    if not default_storage.exists(media.storage_path):
        raise Http404("فایل یافت نشد")

    service.record_download(license_obj)
    file_handle = default_storage.open(media.storage_path, "rb")
    response = FileResponse(file_handle, as_attachment=True, filename=media.original_name)
    response["Content-Type"] = media.mime_type or "application/octet-stream"
    return response


def _optional_user(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Bearer "):
        payload = JWTService().verify_access_token(auth_header[7:])
        if payload:
            return User.objects.filter(pk=int(payload["sub"]), is_active=True).first()
    if getattr(request, "user", None) and request.user.is_authenticated:
        return request.user
    return None
