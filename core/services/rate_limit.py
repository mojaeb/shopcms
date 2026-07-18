"""Cache-backed rate limiting."""

import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    def __init__(self, message: str = "تعداد درخواست بیش از حد مجاز است", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimitService:
    """Simple fixed-window rate limiter using Django cache."""

    def __init__(self, prefix: str = "shopcms:rate"):
        self.prefix = prefix

    def _key(self, scope: str, identifier: str) -> str:
        return f"{self.prefix}:{scope}:{identifier}"

    def hit(self, scope: str, identifier: str, *, limit: int, window_seconds: int) -> None:
        if not getattr(settings, "RATE_LIMIT_ENABLED", True):
            return

        key = self._key(scope, identifier)
        current = cache.get(key, 0)
        if current >= limit:
            raise RateLimitExceeded(retry_after=window_seconds)
        if current == 0:
            cache.set(key, 1, window_seconds)
        else:
            cache.incr(key)

    def is_limited(self, scope: str, identifier: str, *, limit: int, window_seconds: int) -> bool:
        try:
            self.hit(scope, identifier, limit=limit, window_seconds=window_seconds)
        except RateLimitExceeded:
            return True
        return False

    def reset(self, scope: str, identifier: str) -> None:
        cache.delete(self._key(scope, identifier))
