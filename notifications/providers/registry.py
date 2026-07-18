"""Notification provider registry."""

from notifications.providers.base import NotificationProvider

_registry: dict[str, NotificationProvider] = {}


def register(provider_cls):
    instance = provider_cls()
    _registry[provider_cls.codename] = instance
    return provider_cls


def get_provider(codename: str) -> NotificationProvider | None:
    return _registry.get(codename)


def list_providers(channel_type: str | None = None) -> list[NotificationProvider]:
    providers = list(_registry.values())
    if channel_type:
        providers = [p for p in providers if p.channel_type == channel_type]
    return providers
