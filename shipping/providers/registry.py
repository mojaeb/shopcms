"""Provider registry."""

from shipping.providers.base import ShippingProvider

_registry: dict[str, ShippingProvider] = {}


def register(provider_cls):
    instance = provider_cls()
    _registry[provider_cls.codename] = instance
    return provider_cls


def get_provider(codename: str) -> ShippingProvider | None:
    return _registry.get(codename)


def list_providers() -> list[ShippingProvider]:
    return list(_registry.values())
