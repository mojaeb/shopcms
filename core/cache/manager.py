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
        try:
            from django_redis import get_redis_connection

            conn = get_redis_connection("default")
            matched = list(conn.scan_iter(match=pattern, count=500))
            if matched:
                deleted = conn.delete(*matched)
                self._unregister_keys([key.decode() if isinstance(key, bytes) else str(key) for key in matched])
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
        ]
        total = 0
        for pattern in patterns:
            total += self.delete_pattern(pattern)
        return total

    def invalidate_products(self, store_id: int) -> int:
        return self.delete_pattern(f"shopcms:products:{store_id}:*")

    def invalidate_reports(self, store_id: int) -> int:
        return self.delete_pattern(f"shopcms:reports:{store_id}:*")

    def backend_info(self) -> dict:
        backend = settings.CACHES.get("default", {}).get("BACKEND", "")
        location = settings.CACHES.get("default", {}).get("LOCATION", "")
        return {
            "backend": backend.rsplit(".", maxsplit=1)[-1],
            "location": str(location),
            "redis_pattern_delete": "redis" in backend.lower(),
        }


cache_manager = CacheManager()
