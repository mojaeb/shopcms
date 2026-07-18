"""Store admin optimization API."""

from ninja import Router
from ninja.errors import HttpError

from core.services.maintenance import MaintenanceService
from dashboard.authentication_store import store_settings_auth
from tenants.context import get_current_store

router = Router(auth=store_settings_auth)
service = MaintenanceService()


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/status")
def optimization_status(request):
    store = _store(request)
    cache_info = service.cache.backend_info()
    return {
        "store_id": store.id,
        "cache": cache_info,
        "celery_broker": service.cache.get("celery:status") or "not_checked",
    }


@router.post("/cache/warm")
def warm_cache(request):
    store = _store(request)
    result = service.warm_store(store)
    return {"status": "ok", **result}


@router.post("/cache/clear")
def clear_cache(request):
    store = _store(request)
    deleted = service.clear_store_cache(store.id)
    return {"status": "ok", "store_id": store.id, "deleted_keys": deleted}
