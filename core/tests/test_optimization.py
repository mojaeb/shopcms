"""Tests for maintenance service and optimization API."""

import pytest
from django.test import Client

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from core.services.maintenance import MaintenanceService
from django.core.cache import cache
from products.enums import ProductStatus
from products.models import Product
from products.services.search import ProductSearchService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="Opt Shop", slug="opt-shop", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="opt.local")
    return store


@pytest.fixture
def settings_role(db):
    role = Role.objects.create(codename="store_admin", name="Store Admin", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="settings.manage", name="Settings", group="settings")
    role.permissions.add(perm)
    return role


@pytest.fixture
def admin_user(db, store, settings_role):
    user = User.objects.create_user(phone="09120000099", phone_verified=True, is_staff=True)
    StoreMembership.objects.create(
        store=store,
        user=user,
        role=settings_role,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
    )
    return user


@pytest.fixture
def auth_headers(admin_user, store):
    token = JWTService().create_tokens(admin_user.id, store.id, "store_admin", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "opt.local"}


@pytest.mark.django_db
def test_product_filter_options_cached(store):
    Product.objects.create(
        store=store,
        name="Cached Product",
        slug="cached-product",
        status=ProductStatus.ACTIVE,
        base_price=1000,
    )
    service = ProductSearchService()
    key = f"shopcms:products:{store.id}:filter_options:all"

    first = service.get_filter_options(store)
    cache.set(key, {"cached": True}, 60)
    second = service.get_filter_options(store)

    assert first["categories"] == []
    assert second == {"cached": True}


@pytest.mark.django_db
def test_maintenance_warm_store(store):
    service = MaintenanceService()
    result = service.warm_store(store)
    assert result["store_id"] == store.id
    assert "opt.local" in result["domains"]
    assert "cms_storefront" in result["warmed"]

    from cms.services.cache import CMSCacheService

    assert CMSCacheService().get(store.id, "menus") is not None
    assert CMSCacheService().get(store.id, "layout") is not None


@pytest.mark.django_db
def test_optimization_api(client: Client, auth_headers):
    response = client.get("/api/v1/store-admin/optimization/status", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "cache" in data

    warm = client.post("/api/v1/store-admin/optimization/cache/warm", **auth_headers)
    assert warm.status_code == 200
    assert warm.json()["status"] == "ok"

    clear = client.post("/api/v1/store-admin/optimization/cache/clear", **auth_headers)
    assert clear.status_code == 200
    assert clear.json()["status"] == "ok"
