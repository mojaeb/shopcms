"""Plugin management service."""

import logging

from django.db import transaction

from plugins.loader import serialize_manifest
from plugins.registry import get_plugin, list_codenames
from tenants.models import Plugin, Store, StorePlugin

logger = logging.getLogger(__name__)

DEFAULT_ENABLED = {
    "physical": {"physical", "blog", "comments", "payment", "shipping", "coupon", "tax", "inventory"},
    "digital_download": {"digital_download", "blog", "comments", "payment", "coupon", "tax"},
    "subscription": {"subscription", "blog", "comments", "payment", "coupon", "tax"},
    "booking": {"booking", "blog", "comments", "payment", "coupon", "tax"},
    "appointment": {"appointment", "blog", "comments", "payment", "coupon", "tax"},
    "rental": {"rental", "blog", "comments", "payment", "shipping", "coupon", "tax"},
    "print_on_demand": {"print_on_demand", "blog", "comments", "payment", "shipping", "coupon", "tax"},
}


class PluginError(Exception):
    pass


class PluginService:
    """Enable/disable plugins and read manifests for a store."""

    def is_enabled(self, store: Store, codename: str) -> bool:
        return StorePlugin.objects.filter(
            store=store,
            plugin__codename=codename,
            plugin__is_active=True,
            is_enabled=True,
        ).exists()

    def list_enabled_codenames(self, store: Store) -> list[str]:
        return list(
            StorePlugin.objects.filter(store=store, is_enabled=True, plugin__is_active=True)
            .values_list("plugin__codename", flat=True)
            .order_by("plugin__codename")
        )

    def list_for_store(self, store: Store) -> list[dict]:
        enabled_map = {
            sp.plugin_id: sp
            for sp in StorePlugin.objects.filter(store=store).select_related("plugin")
        }
        items = []
        for plugin in Plugin.objects.filter(is_active=True).order_by("name"):
            sp = enabled_map.get(plugin.id)
            registered = serialize_manifest(plugin.codename)
            items.append(
                {
                    "id": plugin.id,
                    "codename": plugin.codename,
                    "name": plugin.name,
                    "description": plugin.description,
                    "is_enabled": sp.is_enabled if sp else False,
                    "is_compatible": plugin.is_compatible_with(store.store_type),
                    "is_registered": registered is not None,
                    "settings": sp.settings if sp else (registered or {}).get("default_settings", {}),
                    "compatible_store_types": plugin.compatible_store_types,
                    "provides": (registered or {}).get("provides", []),
                    "version": (registered or {}).get("version"),
                }
            )
        return items

    @transaction.atomic
    def set_enabled(
        self,
        store: Store,
        codename: str,
        is_enabled: bool,
        settings: dict | None = None,
    ) -> StorePlugin:
        plugin = Plugin.objects.get(codename=codename, is_active=True)
        if not plugin.is_compatible_with(store.store_type):
            raise PluginError("این افزونه با نوع فروشگاه سازگار نیست")

        validated_settings = settings
        registered = get_plugin(codename)
        if registered and settings is not None:
            validated_settings = registered.validate_settings(settings)

        defaults = {"is_enabled": is_enabled}
        if validated_settings is not None:
            defaults["settings"] = validated_settings

        sp, _ = StorePlugin.objects.update_or_create(
            store=store,
            plugin=plugin,
            defaults=defaults,
        )
        logger.info("Plugin %s for store %s set to %s", codename, store.slug, is_enabled)
        return sp

    def get_settings(self, store: Store, codename: str) -> dict:
        sp = StorePlugin.objects.filter(store=store, plugin__codename=codename).select_related("plugin").first()
        if sp:
            return sp.settings
        registered = get_plugin(codename)
        return registered.default_settings() if registered else {}

    @transaction.atomic
    def install_defaults(self, store: Store) -> None:
        enabled = DEFAULT_ENABLED.get(store.store_type, {"blog", "comments", "payment", "coupon", "tax"})
        for plugin in Plugin.objects.filter(is_active=True):
            if not plugin.is_compatible_with(store.store_type):
                continue
            registered = get_plugin(plugin.codename)
            default_settings = registered.default_settings() if registered else {}
            StorePlugin.objects.get_or_create(
                store=store,
                plugin=plugin,
                defaults={
                    "is_enabled": plugin.codename in enabled,
                    "settings": default_settings,
                },
            )

    def sync_registry_to_db(self) -> int:
        """Ensure all registered plugins exist in Plugin table."""
        created = 0
        for codename in list_codenames():
            registered = get_plugin(codename)
            if not registered:
                continue
            manifest = registered.manifest()
            _, was_created = Plugin.objects.update_or_create(
                codename=codename,
                defaults={
                    "name": manifest.name,
                    "description": manifest.description,
                    "compatible_store_types": manifest.compatible_store_types,
                    "is_system": True,
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
        return created

    def serialize_store_plugin(self, sp: StorePlugin) -> dict:
        registered = serialize_manifest(sp.plugin.codename)
        return {
            "id": sp.plugin.id,
            "codename": sp.plugin.codename,
            "name": sp.plugin.name,
            "description": sp.plugin.description,
            "is_enabled": sp.is_enabled,
            "is_compatible": sp.plugin.is_compatible_with(sp.store.store_type),
            "settings": sp.settings,
            "provides": (registered or {}).get("provides", []),
        }
