"""Store resolution and settings service."""

import logging

from django.conf import settings as django_settings

from tenants.context import get_current_store, set_current_store
from tenants.models import Store, StoreSetting
from tenants.repositories.store import DomainRepository, StoreRepository
from tenants.services.cache import StoreCacheService

logger = logging.getLogger(__name__)


class StoreNotFoundError(Exception):
    pass


class StoreInactiveError(Exception):
    pass


class StoreService:
    """Resolve and manage current store context."""

    def __init__(self):
        self.store_repo = StoreRepository()
        self.domain_repo = DomainRepository()
        self.cache_service = StoreCacheService()

    def _load_settings(self, store: Store) -> dict:
        settings = {}
        for item in StoreSetting.objects.filter(store=store):
            settings[item.dotted_key] = item.value
        return settings

    def _cache_store(self, store: Store, domain: str | None = None) -> None:
        settings = self._load_settings(store)
        data = self.cache_service.build_cache_data(store, settings)
        self.cache_service.set_for_store(store.id, data)
        if domain:
            self.cache_service.set_for_domain(domain, data)
        for d in store.domains.filter(is_active=True).values_list("domain", flat=True):
            self.cache_service.set_for_domain(d, data)

    def resolve_by_host(self, host: str) -> Store:
        """Resolve store from request host."""
        host = host.split(":")[0].lower().strip()

        cached = self.cache_service.get_by_domain(host)
        if cached:
            store = self.store_repo.get_active_by_id(cached.id)
            if store:
                return store

        domain = self.domain_repo.get_by_host(host)
        if domain:
            store = domain.store
            self._cache_store(store, host)
            return store

        # Development fallback: map localhost to default store slug
        fallback_slug = getattr(django_settings, "DEFAULT_STORE_SLUG", None)
        if fallback_slug and host in ("localhost", "127.0.0.1"):
            store = self.store_repo.get_by_slug(fallback_slug)
            if store and store.is_active:
                self._cache_store(store, host)
                return store

        raise StoreNotFoundError(f"No store found for host: {host}")

    def resolve_by_slug(self, slug: str) -> Store:
        store = self.store_repo.get_by_slug(slug)
        if not store:
            raise StoreNotFoundError(f"No store found for slug: {slug}")
        if not store.is_active:
            raise StoreInactiveError(f"Store {slug} is not active")
        self._cache_store(store)
        return store

    def activate(self, store: Store) -> None:
        """Set current store in context."""
        set_current_store(store)

    def get_setting(self, key: str, default=None, store: Store | None = None):
        store = store or get_current_store()
        if not store:
            return default
        cached = self.cache_service.get_by_store_id(store.id)
        if cached and key in cached.settings:
            return cached.settings[key]
        try:
            group, setting_key = key.split(".", 1)
            setting = StoreSetting.objects.get(store=store, group=group, key=setting_key)
            return setting.value
        except (StoreSetting.DoesNotExist, ValueError):
            return default

    def set_setting(self, store: Store, group: str, key: str, value, value_type: str = "json"):
        setting, _ = StoreSetting.objects.update_or_create(
            store=store,
            group=group,
            key=key,
            defaults={"value": value, "value_type": value_type},
        )
        self.cache_service.invalidate_store(store)
        return setting
