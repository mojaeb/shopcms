"""Public plugin API."""

from ninja import Router

from plugins.services.plugin import PluginService
from tenants.context import get_current_store

router = Router()
service = PluginService()


@router.get("/active")
def active_plugins(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return {"plugins": []}
    return {"plugins": service.list_enabled_codenames(store)}
