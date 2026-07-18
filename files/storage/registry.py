"""Storage driver registry."""

from files.storage.base import StorageDriverBase

_registry: dict[str, StorageDriverBase] = {}


def register(driver_cls):
    instance = driver_cls()
    _registry[driver_cls.codename] = instance
    return driver_cls


def get_driver(codename: str) -> StorageDriverBase | None:
    return _registry.get(codename)


def list_drivers() -> list[StorageDriverBase]:
    return list(_registry.values())
