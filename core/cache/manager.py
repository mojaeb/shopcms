"""Central cache manager with TTL presets and invalidation helpers."""

import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.core.cache import cache

from core.cache import keys as cache_keys

logger = logging.getLogger(__name__)

DEFAULT_TTL = getattr(settings, "CACHE_DEFAULT_TTL", 900)

TTL = {
    "short": getattr(settings, "CACHE_TTL_SHORT", 300),
    "medium": getattr(settings, "CACHE_TTL_MEDIUM", 900),
    "long": getattr(settings, "CACHE_TTL_LONG", 3600),
    "reports": getattr(settings, "CACHE_TTL_REPORTS", 600),
    "products": getattr(settings, "CACHE_TTL_PRODUCTS", 600),
}


class CacheManager:
    """Unified cache access with namespaced keys and store invalidation."""

    PREFIX = "shopcms"
    REGISTRY_KEY = "shopcms:cache:registry"

    def key(self, *parts: str | int) -> str:
        return ":".join([self.PREFIX, *[str(part) for part in parts if part not in (None, "")]])

    def _register_key(self, key: str) -> None:
        if key == self.REGISTRY_KEY:
            return
        registry = cache.get(self.REGISTRY_KEY, [])
        if key not in registry:
            registry.append(key)
            cache.set(self.REGISTRY_KEY, registry, None)

    def _unregister_keys(self, keys: list[str]) -> None:
        registry = cache.get(self.REGISTRY_KEY, [])
        if not registry:
            return
        remaining = [key for key in registry if key not in keys]
        cache.set(self.REGISTRY_KEY, remaining, None)

    def hash_params(self, params: dict) -> str:
        raw = json.dumps(params, sort_keys=True, default=str)
        return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()[:12]

    def resolve_ttl(self, ttl: int | str | None = None) -> int:
        if isinstance(ttl, str):
            return TTL.get(ttl, DEFAULT_TTL)
        return ttl if ttl is not None else DEFAULT_TTL

    def get(self, key: str, default=None):
        return cache.get(key, default)

    def set(self, key: str, value: Any, ttl: int | str | None = None) -> None:
        cache.set(key, value, self.resolve_ttl(ttl))
        self._register_key(key)

    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: int | str | None = None):
        value = cache.get(key)
        if value is not None:
            return value
        value = factory()
        self.set(key, value, ttl)
        return value

    def delete(self, key: str) -> None:
        cache.delete(key)
        self._unregister_keys([key])

    def delete_many(self, keys: list[str]) -> None:
        if keys:
            cache.delete_many(keys)
            self._unregister_keys(keys)

    def delete_pattern(self, pattern: str) -> int:
        deleted = 0

        # django-redis handles key versioning / prefixes correctly.
        try:
            delete_fn = getattr(cache, "delete_pattern", None)
            if callable(delete_fn):
                deleted = int(delete_fn(pattern) or 0)
                if deleted:
                    prefix = pattern.rstrip("*")
                    registry = cache.get(self.REGISTRY_KEY, [])
                    matched = [key for key in registry if key.startswith(prefix)]
                    self._unregister_keys(matched)
                    return deleted
        except Exception:
            logger.debug("django-redis delete_pattern failed for %s", pattern)

        try:
            from django_redis import get_redis_connection

            conn = get_redis_connection("default")
            # Match both logical keys and versioned keys (:1:shopcms:...)
            patterns = [pattern]
            if not pattern.startswith(":"):
                patterns.append(f"*:{pattern}")
            matched_raw = []
            for pat in patterns:
                matched_raw.extend(list(conn.scan_iter(match=pat, count=500)))
            # Deduplicate
            seen = set()
            unique = []
            for key in matched_raw:
                marker = key if isinstance(key, bytes) else str(key).encode()
                if marker in seen:
                    continue
                seen.add(marker)
                unique.append(key)
            if unique:
                deleted = conn.delete(*unique)
                logical = []
                for key in unique:
                    text = key.decode() if isinstance(key, bytes) else str(key)
                    # Strip django-redis version prefix like ":1:"
                    if text.startswith(":") and text.count(":") >= 2:
                        text = text.split(":", 2)[-1]
                    logical.append(text)
                self._unregister_keys(logical)
                return deleted
        except Exception:
            logger.debug("Pattern delete skipped for %s", pattern)

        prefix = pattern.rstrip("*")
        registry = cache.get(self.REGISTRY_KEY, [])
        matched = [key for key in registry if key.startswith(prefix)]
        if matched:
            cache.delete_many(matched)
            self._unregister_keys(matched)
            deleted = len(matched)
        return deleted

    def invalidate_store(self, store_id: int) -> int:
        patterns = [
            cache_keys.store_namespace(store_id),
            f"shopcms:products:{store_id}:*",
            f"shopcms:reports:{store_id}:*",
            f"shopcms:cms:{store_id}:*",
            f"shopcms:blog:{store_id}:*",
        ]
        total = 0
        for pattern in patterns:
            total += self.delete_pattern(pattern)

        # Bridge older namespaces (store:* / cms:*) used by tenant & CMS services.
        try:
            from cms.services.cache import CMSCacheService
            from cms.services.shortcodes import invalidate_shortcode_cache
            from tenants.models import Store
            from tenants.services.cache import StoreCacheService

            store = Store.objects.filter(pk=store_id).prefetch_related("domains").first()
            if store:
                CMSCacheService().invalidate_store(store)
                StoreCacheService().invalidate_store(store)
                invalidate_shortcode_cache(store)
                total += 1
        except Exception:
            logger.debug("Legacy store/cms cache invalidate failed for store %s", store_id)

        return total

    def invalidate_products(self, store_id: int) -> int:
        return self.delete_pattern(f"shopcms:products:{store_id}:*")

    def invalidate_reports(self, store_id: int) -> int:
        return self.delete_pattern(f"shopcms:reports:{store_id}:*")

    def invalidate_cms(self, store_id: int) -> int:
        total = self.delete_pattern(f"shopcms:cms:{store_id}:*")
        try:
            from cms.services.cache import CMSCacheService
            from cms.services.shortcodes import invalidate_shortcode_cache
            from tenants.models import Store

            store = Store.objects.filter(pk=store_id).first()
            if store:
                CMSCacheService().invalidate_store(store)
                invalidate_shortcode_cache(store)
                total += 1
        except Exception:
            logger.debug("CMS cache invalidate failed for store %s", store_id)
        return total

    def invalidate_blog(self, store_id: int) -> int:
        return self.delete_pattern(f"shopcms:blog:{store_id}:*")

    def backend_info(self) -> dict:
        backend = settings.CACHES.get("default", {}).get("BACKEND", "")
        location = settings.CACHES.get("default", {}).get("LOCATION", "")
        return {
            "backend": backend.rsplit(".", maxsplit=1)[-1],
            "location": str(location),
            "redis_pattern_delete": "redis" in backend.lower(),
        }


cache_manager = CacheManager()
