"""Store cache service."""

import logging
from dataclasses import asdict, dataclass
from typing import Any

from django.core.cache import cache

from tenants.models import Store

logger = logging.getLogger(__name__)

CACHE_PREFIX = "store"
CACHE_TTL = 60 * 15  # 15 minutes


@dataclass
class StoreCacheData:
    id: int
    name: str
    slug: str
    store_type: str
    status: str
    theme_slug: str
    currency: str
    timezone: str
    language: str
    tax_enabled: bool
    tax_percent: str
    settings: dict[str, Any]


class StoreCacheService:
    """Cache store data by domain for fast middleware resolution."""

    @staticmethod
    def _domain_key(domain: str) -> str:
        return f"{CACHE_PREFIX}:domain:{domain.lower()}"

    @staticmethod
    def _store_key(store_id: int) -> str:
        return f"{CACHE_PREFIX}:id:{store_id}"

    def build_cache_data(self, store: Store, settings: dict | None = None) -> StoreCacheData:
        return StoreCacheData(
            id=store.id,
            name=store.name,
            slug=store.slug,
            store_type=store.store_type,
            status=store.status,
            theme_slug=store.effective_theme_slug,
            currency=store.currency,
            timezone=store.timezone,
            language=store.language,
            tax_enabled=store.tax_enabled,
            tax_percent=str(store.tax_percent),
            settings=settings or {},
        )

    def set_for_domain(self, domain: str, data: StoreCacheData) -> None:
        cache.set(self._domain_key(domain), asdict(data), CACHE_TTL)

    def get_by_domain(self, domain: str) -> StoreCacheData | None:
        raw = cache.get(self._domain_key(domain))
        if raw is None:
            return None
        return StoreCacheData(**raw)

    def set_for_store(self, store_id: int, data: StoreCacheData) -> None:
        cache.set(self._store_key(store_id), asdict(data), CACHE_TTL)

    def get_by_store_id(self, store_id: int) -> StoreCacheData | None:
        raw = cache.get(self._store_key(store_id))
        if raw is None:
            return None
        return StoreCacheData(**raw)

    def invalidate_store(self, store: Store) -> None:
        keys = [self._store_key(store.id)]
        for domain in store.domains.values_list("domain", flat=True):
            keys.append(self._domain_key(domain))
        cache.delete_many(keys)
        logger.info("Invalidated cache for store %s (%d keys)", store.slug, len(keys))

    def invalidate_domain(self, domain: str) -> None:
        cache.delete(self._domain_key(domain.lower()))
