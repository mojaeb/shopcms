"""Customer download API."""

from ninja import Router
from ninja.errors import HttpError

from accounts.models import User
from accounts.services.jwt import JWTService
from digital.services.digital import DigitalError, DigitalService
from tenants.context import get_current_store

router = Router()
service = DigitalService()


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


def _user(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Bearer "):
        payload = JWTService().verify_access_token(auth_header[7:])
        if payload:
            user = User.objects.filter(pk=int(payload["sub"]), is_active=True).first()
            if user:
                return user
    if getattr(request, "user", None) and request.user.is_authenticated:
        return request.user
    raise HttpError(401, "ورود الزامی است")


@router.get("/")
def list_downloads(request):
    store = _store(request)
    if not service.is_active(store):
        return []
    user = _user(request)
    licenses = service.list_user_licenses(user, store)
    return [service.serialize_license(lic) for lic in licenses]


@router.get("/{token}")
def download_info(request, token: str):
    store = _store(request)
    user = _user(request)
    try:
        lic = service.validate_download(token, user=user)
        if lic.store_id != store.id:
            raise HttpError(404, "مجوز یافت نشد")
        return service.serialize_license(lic)
    except DigitalError as exc:
        raise HttpError(400, str(exc))
