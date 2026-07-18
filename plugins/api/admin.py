"""Store admin plugin API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from dashboard.authentication_store import store_admin_auth, store_settings_auth
from plugins.loader import list_registry_manifests, serialize_manifest
from plugins.services.plugin import PluginError, PluginService
from tenants.context import get_current_store
from tenants.models import Plugin

router = Router()
service = PluginService()


class PluginToggleSchema(Schema):
    is_enabled: bool
    settings: dict | None = None


class PluginItemSchema(Schema):
    id: int
    codename: str
    name: str
    description: str
    is_enabled: bool
    is_compatible: bool
    is_registered: bool
    settings: dict
    compatible_store_types: list
    provides: list
    version: str | None = None


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("", response=list[PluginItemSchema], auth=store_admin_auth)
def list_store_plugins(request):
    return service.list_for_store(_store(request))


@router.put("/{codename}", auth=store_settings_auth)
def update_plugin(request, codename: str, payload: PluginToggleSchema):
    store = _store(request)
    try:
        sp = service.set_enabled(store, codename, payload.is_enabled, payload.settings)
        return service.serialize_store_plugin(sp)
    except Plugin.DoesNotExist:
        raise HttpError(404, "افزونه یافت نشد")
    except PluginError as exc:
        raise HttpError(400, str(exc))
    except ValueError as exc:
        raise HttpError(400, str(exc))


@router.get("/registry", auth=store_admin_auth)
def plugin_registry(request):
    return list_registry_manifests()


@router.get("/{codename}/manifest", auth=store_admin_auth)
def plugin_manifest(request, codename: str):
    manifest = serialize_manifest(codename)
    if not manifest:
        raise HttpError(404, "افزونه در رجیستری یافت نشد")
    return manifest
