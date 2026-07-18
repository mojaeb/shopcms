"""Plugin registry."""

from plugins.base import BasePlugin

_registry: dict[str, BasePlugin] = {}


def register(plugin_cls):
    instance = plugin_cls()
    if not instance.codename:
        raise ValueError(f"Plugin {plugin_cls.__name__} missing codename")
    _registry[instance.codename] = instance
    return plugin_cls


def get_plugin(codename: str) -> BasePlugin | None:
    return _registry.get(codename)


def list_plugins() -> list[BasePlugin]:
    return list(_registry.values())


def list_codenames() -> list[str]:
    return sorted(_registry.keys())
