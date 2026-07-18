"""Super Admin service layer."""

import logging
from typing import Any

from django.db import transaction
from django.db.models import Count, Q

from accounts.services.auth import AuthService
from tenants.enums import StoreStatus
from tenants.models import Domain, Plugin, Store, StorePlugin, StoreSetting, Theme
from tenants.services.cache import StoreCacheService

logger = logging.getLogger(__name__)


class SuperAdminError(Exception):
    pass


class StoreNotFoundError(SuperAdminError):
    pass


class SuperAdminService:
    """Platform-level store and configuration management."""

    def __init__(self):
        self.cache_service = StoreCacheService()
        self.auth_service = AuthService()

    def list_stores(self, search: str = "", status: str | None = None):
        qs = Store.objects.select_related("theme", "default_theme").annotate(
            domain_count=Count("domains"),
            member_count=Count("memberships"),
        )
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search))
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")

    def get_store(self, store_id: int) -> Store:
        try:
            return Store.objects.select_related("theme", "default_theme").get(pk=store_id)
        except Store.DoesNotExist:
            raise StoreNotFoundError(f"Store {store_id} not found")

    @transaction.atomic
    def create_store(self, data: dict) -> Store:
        theme = None
        default_theme = None

        if data.get("theme_id"):
            theme = Theme.objects.get(pk=data["theme_id"])
        if data.get("default_theme_id"):
            default_theme = Theme.objects.get(pk=data["default_theme_id"])
        elif not default_theme:
            default_theme = Theme.objects.filter(is_default=True).first()

        store = Store.objects.create(
            name=data["name"],
            slug=data["slug"],
            store_type=data.get("store_type", "physical"),
            theme=theme,
            default_theme=default_theme,
            currency=data.get("currency", "IRR"),
            timezone=data.get("timezone", "Asia/Tehran"),
            language=data.get("language", "fa"),
            status=data.get("status", StoreStatus.ACTIVE),
            tax_enabled=data.get("tax_enabled", False),
            tax_percent=data.get("tax_percent", 0),
        )

        for domain_name in data.get("domains", []):
            Domain.objects.create(store=store, domain=domain_name.lower())

        self._auto_enable_plugins(store)
        logger.info("Store created: %s", store.slug)
        return store

    @transaction.atomic
    def update_store(self, store_id: int, data: dict) -> Store:
        store = self.get_store(store_id)

        for field in ("name", "slug", "store_type", "currency", "timezone", "language", "status"):
            if field in data and data[field] is not None:
                setattr(store, field, data[field])

        if "tax_enabled" in data:
            store.tax_enabled = data["tax_enabled"]
        if "tax_percent" in data:
            store.tax_percent = data["tax_percent"]
        if "theme_id" in data:
            store.theme_id = data["theme_id"]
        if "default_theme_id" in data:
            store.default_theme_id = data["default_theme_id"]

        store.save()
        self.cache_service.invalidate_store(store)
        return store

    @transaction.atomic
    def delete_store(self, store_id: int, hard: bool = False) -> None:
        store = self.get_store(store_id)
        if hard:
            store.delete()
        else:
            store.status = StoreStatus.INACTIVE
            store.save(update_fields=["status", "updated_at"])
            self.cache_service.invalidate_store(store)
        logger.info("Store deleted/deactivated: %s", store.slug)

    def list_domains(self, store_id: int):
        return Domain.objects.filter(store_id=store_id).order_by("-is_primary", "domain")

    @transaction.atomic
    def add_domain(self, store_id: int, data: dict) -> Domain:
        store = self.get_store(store_id)
        domain = Domain.objects.create(
            store=store,
            domain=data["domain"].lower().strip(),
            is_primary=data.get("is_primary", False),
            ssl_enabled=data.get("ssl_enabled", True),
            redirect_to_primary=data.get("redirect_to_primary", False),
            is_active=data.get("is_active", True),
        )
        self.cache_service.invalidate_store(store)
        return domain

    def update_domain(self, store_id: int, domain_id: int, data: dict) -> Domain:
        domain = Domain.objects.get(pk=domain_id, store_id=store_id)
        for field in ("domain", "is_primary", "ssl_enabled", "redirect_to_primary", "is_active"):
            if field in data and data[field] is not None:
                setattr(domain, field, data[field])
        domain.save()
        self.cache_service.invalidate_store(domain.store)
        return domain

    def delete_domain(self, store_id: int, domain_id: int) -> None:
        domain = Domain.objects.get(pk=domain_id, store_id=store_id)
        store = domain.store
        domain.delete()
        self.cache_service.invalidate_store(store)

    def create_store_admin(self, store_id: int, data: dict) -> dict:
        store = self.get_store(store_id)
        user, membership = self.auth_service.create_store_admin(
            phone=data["phone"],
            store=store,
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            is_primary=data.get("is_primary", False),
        )
        return {"user": user, "membership": membership}

    def list_store_admins(self, store_id: int):
        from accounts.models import StoreMembership

        return (
            StoreMembership.objects.select_related("user", "role")
            .filter(store_id=store_id, role__codename="store_admin")
            .order_by("-is_primary", "-created_at")
        )

    def list_themes(self):
        return Theme.objects.filter(is_active=True).order_by("name")

    def list_plugins(self, store_type: str | None = None):
        qs = Plugin.objects.filter(is_active=True)
        if store_type:
            qs = [p for p in qs if p.is_compatible_with(store_type)]
        return qs

    def list_store_plugins(self, store_id: int):
        store = self.get_store(store_id)
        enabled = {sp.plugin_id: sp for sp in StorePlugin.objects.filter(store=store).select_related("plugin")}
        result = []
        for plugin in Plugin.objects.filter(is_active=True):
            if not plugin.is_compatible_with(store.store_type):
                continue
            sp = enabled.get(plugin.id)
            result.append({
                "plugin": plugin,
                "is_enabled": sp.is_enabled if sp else False,
                "settings": sp.settings if sp else {},
                "store_plugin_id": sp.id if sp else None,
            })
        return result

    @transaction.atomic
    def set_store_plugin(self, store_id: int, plugin_id: int, is_enabled: bool, settings: dict | None = None):
        store = self.get_store(store_id)
        plugin = Plugin.objects.get(pk=plugin_id)

        if not plugin.is_compatible_with(store.store_type):
            raise SuperAdminError(f"Plugin {plugin.codename} is not compatible with {store.store_type}")

        sp, _ = StorePlugin.objects.update_or_create(
            store=store,
            plugin=plugin,
            defaults={
                "is_enabled": is_enabled,
                "settings": settings or {},
            },
        )
        return sp

    def get_tax_settings(self, store_id: int) -> dict:
        store = self.get_store(store_id)
        return {
            "tax_enabled": store.tax_enabled,
            "tax_percent": str(store.tax_percent),
        }

    @transaction.atomic
    def update_tax_settings(self, store_id: int, data: dict) -> dict:
        store = self.get_store(store_id)
        if "tax_enabled" in data:
            store.tax_enabled = data["tax_enabled"]
        if "tax_percent" in data:
            store.tax_percent = data["tax_percent"]
        store.save(update_fields=["tax_enabled", "tax_percent", "updated_at"])
        self.cache_service.invalidate_store(store)
        return self.get_tax_settings(store_id)

    def get_group_settings(self, store_id: int, group: str) -> dict:
        store = self.get_store(store_id)
        settings = {}
        for item in StoreSetting.objects.filter(store=store, group=group):
            settings[item.key] = item.value
        return settings

    @transaction.atomic
    def update_group_settings(self, store_id: int, group: str, data: dict) -> dict:
        store = self.get_store(store_id)
        for key, value in data.items():
            StoreSetting.objects.update_or_create(
                store=store,
                group=group,
                key=key,
                defaults={"value": value, "value_type": "json"},
            )
        self.cache_service.invalidate_store(store)
        return self.get_group_settings(store_id, group)

    def get_payment_settings(self, store_id: int) -> dict:
        defaults = {
            "gateways": [],
            "default_gateway": "",
            "zarinpal": {"merchant_id": "", "sandbox": True},
            "idpay": {"api_key": "", "sandbox": True},
            "mellat": {"terminal_id": "", "username": "", "password": ""},
        }
        saved = self.get_group_settings(store_id, "payment")
        return {**defaults, **saved}

    def update_payment_settings(self, store_id: int, data: dict) -> dict:
        return self.update_group_settings(store_id, "payment", data)

    def get_shipping_settings(self, store_id: int) -> dict:
        defaults = {
            "providers": [],
            "default_provider": "",
            "post": {"mode": "fixed", "fixed_price": 0, "distance_table": []},
            "tipax": {"mode": "distance", "api_key": ""},
            "free_shipping_threshold": 0,
        }
        saved = self.get_group_settings(store_id, "shipping")
        return {**defaults, **saved}

    def update_shipping_settings(self, store_id: int, data: dict) -> dict:
        return self.update_group_settings(store_id, "shipping", data)

    def _auto_enable_plugins(self, store: Store) -> None:
        from plugins.services.plugin import PluginService

        PluginService().install_defaults(store)

    def get_dashboard_stats(self) -> dict:
        return {
            "total_stores": Store.objects.count(),
            "active_stores": Store.objects.filter(status=StoreStatus.ACTIVE).count(),
            "inactive_stores": Store.objects.filter(status=StoreStatus.INACTIVE).count(),
            "total_domains": Domain.objects.count(),
            "total_themes": Theme.objects.filter(is_active=True).count(),
            "total_plugins": Plugin.objects.filter(is_active=True).count(),
        }
