"""Store admin digital products API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from dashboard.authentication_store import store_products_auth
from digital.services.digital import DigitalError, DigitalService
from tenants.context import get_current_store

router = Router(auth=store_products_auth)
service = DigitalService()


class AssetAttachSchema(Schema):
    media_file_id: int
    title: str = ""
    max_downloads: int | None = None
    expire_hours: int | None = None


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/products/{product_id}/assets")
def list_assets(request, product_id: int):
    store = _store(request)
    assets = service.list_product_assets(store, product_id)
    return [service.serialize_asset(a) for a in assets]


@router.post("/products/{product_id}/assets")
def attach_asset(request, product_id: int, payload: AssetAttachSchema):
    store = _store(request)
    try:
        asset = service.attach_asset(
            store,
            product_id,
            payload.media_file_id,
            title=payload.title,
            max_downloads=payload.max_downloads,
            expire_hours=payload.expire_hours,
        )
        return service.serialize_asset(asset)
    except Exception as exc:
        raise HttpError(400, str(exc))


@router.delete("/products/{product_id}/assets/{asset_id}")
def detach_asset(request, product_id: int, asset_id: int):
    store = _store(request)
    service.detach_asset(store, product_id, asset_id)
    return {"success": True}


@router.get("/licenses")
def list_licenses(request, order_id: int | None = None):
    store = _store(request)
    from digital.models import DownloadLicense

    qs = DownloadLicense.objects.filter(store=store).select_related("media_file", "user", "order")
    if order_id:
        qs = qs.filter(order_id=order_id)
    return [
        {
            **service.serialize_license(lic),
            "user_phone": lic.user.phone,
        }
        for lic in qs.order_by("-created_at")[:100]
    ]


@router.post("/licenses/{license_id}/revoke")
def revoke_license(request, license_id: int):
    store = _store(request)
    try:
        lic = service.revoke_license(store, license_id)
        return service.serialize_license(lic)
    except DigitalError as exc:
        raise HttpError(404, str(exc))
