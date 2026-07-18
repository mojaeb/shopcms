"""Rate limit service tests."""

import pytest
from django.core.cache import cache

from core.services.rate_limit import RateLimitExceeded, RateLimitService


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_rate_limit_allows_under_threshold(settings):
    settings.RATE_LIMIT_ENABLED = True
    service = RateLimitService()
    service.hit("test", "user1", limit=3, window_seconds=60)
    service.hit("test", "user1", limit=3, window_seconds=60)
    service.hit("test", "user1", limit=3, window_seconds=60)


def test_rate_limit_blocks_over_threshold(settings):
    settings.RATE_LIMIT_ENABLED = True
    service = RateLimitService()
    for _ in range(2):
        service.hit("test", "user2", limit=2, window_seconds=60)
    with pytest.raises(RateLimitExceeded):
        service.hit("test", "user2", limit=2, window_seconds=60)


def test_rate_limit_disabled(settings):
    settings.RATE_LIMIT_ENABLED = False
    service = RateLimitService()
    for _ in range(10):
        service.hit("test", "user3", limit=1, window_seconds=60)
