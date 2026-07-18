"""Platform maintenance helpers for cache warmup and cleanup."""

import logging
import tempfile
import time
from pathlib import Path

from django.conf import settings

from core.cache import cache_manager
from products.services.search import ProductSearchService
from tenants.enums import StoreStatus
from tenants.models import Store
from tenants.services.store import StoreService

logger = logging.getLogger(__name__)


class MaintenanceService:
    """Warm caches and clean temporary files."""

    def __init__(self):
        self.cache = cache_manager
        self.store_service = StoreService()
        self.product_search = ProductSearchService()

    def warm_store(self, store: Store) -> dict:
        self.store_service._cache_store(store)
        self.product_search.get_filter_options(store)
        return {
            "store_id": store.id,
            "store_slug": store.slug,
            "domains": list(store.domains.values_list("domain", flat=True)),
        }

    def warm_active_stores(self, store_slug: str | None = None) -> dict:
        qs = Store.objects.filter(status=StoreStatus.ACTIVE).prefetch_related("domains")
        if store_slug:
            qs = qs.filter(slug=store_slug)

        warmed = []
        for store in qs:
            warmed.append(self.warm_store(store))

        return {"warmed_stores": len(warmed), "stores": warmed}

    def clear_store_cache(self, store_id: int) -> int:
        return self.cache.invalidate_store(store_id)

    def clear_all_cache(self) -> int:
        return self.cache.delete_pattern(f"{self.cache.PREFIX}:*")

    def cleanup_temp_files(self, max_age_hours: int = 24) -> dict:
        cutoff = time.time() - (max_age_hours * 3600)
        removed = 0
        scanned = 0

        targets = [
            Path(tempfile.gettempdir()),
            Path(settings.MEDIA_ROOT) / "tmp",
        ]

        for base in targets:
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                scanned += 1
                name = path.name.lower()
                if not (name.startswith("shopcms") or name.startswith("tmp") or "upload" in name):
                    continue
                try:
                    if path.stat().st_mtime < cutoff:
                        path.unlink(missing_ok=True)
                        removed += 1
                except OSError as exc:
                    logger.warning("Failed to remove temp file %s: %s", path, exc)

        return {"scanned": scanned, "removed": removed, "max_age_hours": max_age_hours}
