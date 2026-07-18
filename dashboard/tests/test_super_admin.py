"""Tests for Super Admin API."""

import pytest

from accounts.models import User
from accounts.services.jwt import JWTService
from tenants.models import Domain, Plugin, Store, Theme


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(phone="09120000000", password="admin123")


@pytest.fixture
def super_token(superuser):
    return JWTService().create_tokens(superuser.id).access_token


@pytest.fixture
def default_theme(db):
    return Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)


@pytest.fixture
def sample_store(db, default_theme):
    store = Store.objects.create(name="Test Store", slug="test-store", default_theme=default_theme, status="active")
    Domain.objects.create(store=store, domain="test.local", is_primary=True)
    return store


@pytest.fixture
def plugins(db):
    Plugin.objects.create(codename="physical", name="Physical", compatible_store_types=["physical"])
    Plugin.objects.create(codename="blog", name="Blog", compatible_store_types=[])


@pytest.mark.django_db
def test_dashboard_stats(client, super_token, sample_store):
    response = client.get(
        "/api/v1/super-admin/stats",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_stores"] >= 1


@pytest.mark.django_db
def test_create_store(client, super_token, default_theme, plugins):
    response = client.post(
        "/api/v1/super-admin/stores",
        data={
            "name": "New Shop",
            "slug": "new-shop",
            "store_type": "physical",
            "default_theme_id": default_theme.id,
            "domains": ["newshop.local"],
            "tax_enabled": True,
            "tax_percent": 9,
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "new-shop"
    assert data["tax_enabled"] is True
    assert Store.objects.filter(slug="new-shop").exists()
    assert Domain.objects.filter(domain="newshop.local").exists()


@pytest.mark.django_db
def test_update_and_delete_store(client, super_token, sample_store):
    response = client.put(
        f"/api/v1/super-admin/stores/{sample_store.id}",
        data={"name": "Updated Store", "status": "suspended"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Store"

    response = client.delete(
        f"/api/v1/super-admin/stores/{sample_store.id}",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200
    sample_store.refresh_from_db()
    assert sample_store.status == "inactive"


@pytest.mark.django_db
def test_domain_crud(client, super_token, sample_store):
    response = client.post(
        f"/api/v1/super-admin/stores/{sample_store.id}/domains",
        data={"domain": "shop2.local", "is_primary": False},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200
    domain_id = response.json()["id"]

    response = client.delete(
        f"/api/v1/super-admin/stores/{sample_store.id}/domains/{domain_id}",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_create_store_admin(client, super_token, sample_store):
    response = client.post(
        f"/api/v1/super-admin/stores/{sample_store.id}/admins",
        data={"phone": "09123334444", "first_name": "Admin", "last_name": "User", "is_primary": True},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200
    assert response.json()["phone"] == "09123334444"


@pytest.mark.django_db
def test_plugin_management(client, super_token, sample_store, plugins):
    plugin = Plugin.objects.get(codename="blog")
    response = client.put(
        f"/api/v1/super-admin/stores/{sample_store.id}/plugins/{plugin.id}",
        data={"is_enabled": True, "settings": {"show_on_home": True}},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200
    assert response.json()["is_enabled"] is True


@pytest.mark.django_db
def test_payment_shipping_settings(client, super_token, sample_store):
    response = client.put(
        f"/api/v1/super-admin/stores/{sample_store.id}/settings/payment",
        data={
            "gateways": ["zarinpal", "idpay"],
            "default_gateway": "zarinpal",
            "zarinpal": {"merchant_id": "test-merchant", "sandbox": True},
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200
    assert "zarinpal" in response.json()["gateways"]

    response = client.put(
        f"/api/v1/super-admin/stores/{sample_store.id}/settings/shipping",
        data={
            "providers": ["post", "tipax"],
            "default_provider": "post",
            "post": {"mode": "fixed", "fixed_price": 50000},
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {super_token}",
    )
    assert response.status_code == 200
    assert response.json()["default_provider"] == "post"


@pytest.mark.django_db
def test_unauthorized_access(client, sample_store):
    response = client.get("/api/v1/super-admin/stats")
    assert response.status_code == 401

    user = User.objects.create_user(phone="09128888888")
    token = JWTService().create_tokens(user.id).access_token
    response = client.get(
        "/api/v1/super-admin/stats",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 401
