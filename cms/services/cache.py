"""CMS data cache."""

from django.core.cache import cache

CACHE_PREFIX = "cms"
CACHE_TTL = 60 * 10


class CMSCacheService:
    def _key(self, store_id: int, suffix: str) -> str:
        return f"{CACHE_PREFIX}:{store_id}:{suffix}"

    def get(self, store_id: int, suffix: str):
        return cache.get(self._key(store_id, suffix))

    def set(self, store_id: int, suffix: str, data) -> None:
        cache.set(self._key(store_id, suffix), data, CACHE_TTL)

    def invalidate_store(self, store) -> None:
        keys = [
            self._key(store.id, "menus"),
            self._key(store.id, "banners"),
            self._key(store.id, "sliders"),
            self._key(store.id, "layout"),
            self._key(store.id, "home_blocks"),
        ]
        cache.delete_many(keys)
