"""Resolve storage driver for a store."""

from files.enums import StorageDriver
from files.storage.registry import get_driver, list_drivers
from tenants.models import StoreSetting


class StorageManager:
    """Pick and configure the storage backend for a store."""

    DEFAULT_DRIVER = StorageDriver.LOCAL

    def get_store_config(self, store) -> dict:
        try:
            setting = StoreSetting.objects.get(store=store, group="storage", key="driver")
            value = setting.value
            if isinstance(value, dict):
                return value
        except StoreSetting.DoesNotExist:
            pass
        return {"driver": self.DEFAULT_DRIVER}

    def get_driver_for_store(self, store):
        config = self.get_store_config(store)
        codename = config.get("driver", self.DEFAULT_DRIVER)
        driver = get_driver(codename)
        if not driver:
            driver = get_driver(self.DEFAULT_DRIVER)
        driver.validate_config(config)
        return driver, config

    def list_available_drivers(self) -> list[dict]:
        return [{"codename": d.codename, "label": d.label} for d in list_drivers()]
