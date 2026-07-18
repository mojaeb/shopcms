"""Tests for cache manager."""

import pytest
from django.core.cache import cache

from core.cache import cache_manager
from core.cache.keys import product_filter_options, report_summary


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_cache_get_or_set():
    calls = {"count": 0}

    def factory():
        calls["count"] += 1
        return {"value": 1}

    first = cache_manager.get_or_set("shopcms:test:key", factory, ttl="short")
    second = cache_manager.get_or_set("shopcms:test:key", factory, ttl="short")

    assert first == {"value": 1}
    assert second == {"value": 1}
    assert calls["count"] == 1


def test_cache_key_builders():
    assert product_filter_options(1, "phones") == "shopcms:products:1:filter_options:phones"
    assert report_summary(2, 30) == "shopcms:reports:2:summary:30"


def test_backend_info():
    info = cache_manager.backend_info()
    assert "backend" in info
    assert "location" in info
