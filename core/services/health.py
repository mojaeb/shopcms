"""Health check service."""

import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.db import connection

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    status: str
    database: str
    cache: str
    version: str = "0.1.0"
    cache_backend: str = ""
    celery: str = "not_checked"


class HealthService:
    """Check platform health status."""

    def check_database(self) -> str:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return "ok"
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            return "error"

    def check_cache(self) -> str:
        try:
            cache.set("health_check", "ok", timeout=10)
            result = cache.get("health_check")
            return "ok" if result == "ok" else "error"
        except Exception as e:
            logger.error("Cache health check failed: %s", e)
            return "error"

    def check_celery(self) -> str:
        broker_url = getattr(settings, "CELERY_BROKER_URL", "")
        if not broker_url:
            return "not_configured"
        if broker_url.startswith("redis://"):
            try:
                from django_redis import get_redis_connection

                conn = get_redis_connection("default")
                conn.ping()
                return "ok"
            except Exception as e:
                logger.warning("Celery broker redis ping failed: %s", e)
                return "error"
        return "unknown"

    def get_status(self) -> HealthStatus:
        db_status = self.check_database()
        cache_status = self.check_cache()
        cache_backend = settings.CACHES.get("default", {}).get("BACKEND", "")
        celery_status = self.check_celery()

        overall = "healthy" if db_status == "ok" and cache_status == "ok" else "unhealthy"

        return HealthStatus(
            status=overall,
            database=db_status,
            cache=cache_status,
            version=getattr(settings, "PLATFORM_VERSION", "0.1.0"),
            cache_backend=cache_backend.rsplit(".", maxsplit=1)[-1],
            celery=celery_status,
        )
