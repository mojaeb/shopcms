"""Load plugins and wire routers, URLs, and events."""

from django.urls import include, path

from plugins.registry import get_plugin, list_plugins

_loaded = False


def load_plugins() -> None:
    global _loaded
    if _loaded:
        return
    import plugins.builtin  # noqa: F401

    for plugin in list_plugins():
        plugin.register_events()
    _loaded = True


def register_api_routers(api) -> None:
    load_plugins()
    for plugin in list_plugins():
        router = plugin.get_api_router()
        if router:
            prefix = f"/plugins/{plugin.codename}"
            api.add_router(prefix, router, tags=[f"Plugin:{plugin.name}"])


def get_plugin_urlpatterns() -> list:
    load_plugins()
    patterns = []
    for plugin in list_plugins():
        urls = plugin.get_urlpatterns()
        if urls:
            patterns.append(path(f"plugins/{plugin.codename}/", include((urls, plugin.codename))))
    return patterns


def serialize_manifest(codename: str) -> dict | None:
    plugin = get_plugin(codename)
    if not plugin:
        return None
    manifest = plugin.manifest()
    return {
        "codename": manifest.codename,
        "name": manifest.name,
        "description": manifest.description,
        "version": manifest.version,
        "compatible_store_types": manifest.compatible_store_types,
        "provides": manifest.provides,
        "settings_schema": [
            {
                "key": f.key,
                "label": f.label,
                "field_type": f.field_type,
                "default": f.default,
                "required": f.required,
                "help_text": f.help_text,
            }
            for f in manifest.settings_schema
        ],
        "default_settings": plugin.default_settings(),
    }


def list_registry_manifests() -> list[dict]:
    load_plugins()
    return [serialize_manifest(p.codename) for p in list_plugins() if serialize_manifest(p.codename)]
