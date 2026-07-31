"""Tests for cache manager."""

import pytest
from django.core.cache import cache

from cms.services.cache import CMSCacheService
from core.cache import cache_manager
from core.cache.keys import (
    blog_detail,
    cms_page,
    product_detail,
    product_filter_options,
    product_list,
    report_summary,
)
from tenants.models import Domain, Store, Theme
from tenants.services.cache import StoreCacheService


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="Cache Shop", slug="cache-shop", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="cache.local")
    return store


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
    assert product_list(1, "abc") == "shopcms:products:1:list:abc"
    assert product_detail(1, "slug") == "shopcms:products:1:detail:slug"
    assert cms_page(1, "about") == "shopcms:cms:1:page:about"
    assert blog_detail(1, "hello") == "shopcms:blog:1:detail:hello"


def test_backend_info():
    info = cache_manager.backend_info()
    assert "backend" in info
    assert "location" in info


@pytest.mark.django_db
def test_invalidate_store_clears_legacy_namespaces(store):
    cache_manager.set(f"shopcms:products:{store.id}:list:x", {"ok": True}, ttl="short")
    cache_manager.set(cms_page(store.id, "about"), {"slug": "about"}, ttl="medium")
    cache_manager.set(blog_detail(store.id, "hello"), {"slug": "hello"}, ttl="medium")

    CMSCacheService().set(store.id, "menus", {"header": {}})
    StoreCacheService().set_for_store(
        store.id,
        StoreCacheService().build_cache_data(store),
    )
    cache.set(f"cms:{store.id}:shortcodes", {"x": 1}, 60)

    deleted = cache_manager.invalidate_store(store.id)
    assert deleted >= 1

    assert cache_manager.get(f"shopcms:products:{store.id}:list:x") is None
    assert cache_manager.get(cms_page(store.id, "about")) is None
    assert cache_manager.get(blog_detail(store.id, "hello")) is None
    assert CMSCacheService().get(store.id, "menus") is None
    assert StoreCacheService().get_by_store_id(store.id) is None
    assert cache.get(f"cms:{store.id}:shortcodes") is None


@pytest.mark.django_db
def test_delete_pattern_via_registry():
    cache_manager.set("shopcms:products:99:list:a", 1, ttl="short")
    cache_manager.set("shopcms:products:99:detail:x", 2, ttl="short")
    cache_manager.set("shopcms:products:100:list:a", 3, ttl="short")

    deleted = cache_manager.invalidate_products(99)
    assert deleted == 2
    assert cache_manager.get("shopcms:products:99:list:a") is None
    assert cache_manager.get("shopcms:products:100:list:a") == 3
