"""Tests for Store Admin panel API."""

import pytest

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def setup_store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="Shop One", slug="shop1", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="localhost", is_primary=True)
    return store


@pytest.fixture
def roles(db):
    admin = Role.objects.create(name="Admin", codename="store_admin", scope=RoleScope.STORE, is_system=True)
    customer = Role.objects.create(name="Customer", codename="customer", scope=RoleScope.STORE, is_system=True)
    products = Role.objects.create(name="Products", codename="products", scope=RoleScope.STORE, is_system=True)
    perm = Permission.objects.create(codename="products.view", name="View Products", group="products")
    products.permissions.add(perm)
    settings_perm = Permission.objects.create(codename="settings.manage", name="Manage Settings", group="settings")
    admin_role_with_perm = admin
    return {
        "store_admin": admin_role_with_perm,
        "customer": customer,
        "products": products,
        "settings_perm": settings_perm,
    }


@pytest.fixture
def store_admin_user(setup_store, roles):
    user = User.objects.create_user(phone="09121112222", first_name="Admin", is_staff=True)
    membership = StoreMembership.objects.create(
        user=user, store=setup_store, role=roles["store_admin"], status=MembershipStatus.ACTIVE, is_primary=True
    )
    return user, membership


@pytest.fixture
def customer_user(setup_store, roles):
    user = User.objects.create_user(phone="09123334444", first_name="Customer")
    membership = StoreMembership.objects.create(
        user=user, store=setup_store, role=roles["customer"], status=MembershipStatus.ACTIVE
    )
    return user, membership


@pytest.fixture
def admin_token(store_admin_user, setup_store):
    user, membership = store_admin_user
    return JWTService().create_tokens(
        user.id, setup_store.id, "store_admin", membership.id
    ).access_token


@pytest.fixture
def customer_token(customer_user, setup_store):
    user, membership = customer_user
    return JWTService().create_tokens(
        user.id, setup_store.id, "customer", membership.id
    ).access_token


@pytest.mark.django_db
def test_dashboard_stats(client, admin_token, setup_store, customer_user):
    response = client.get(
        "/api/v1/store-admin/dashboard",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["store_slug"] == "shop1"
    assert data["total_customers"] >= 1


@pytest.mark.django_db
def test_customer_denied(client, customer_token):
    response = client.get(
        "/api/v1/store-admin/dashboard",
        HTTP_AUTHORIZATION=f"Bearer {customer_token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_settings_update(client, admin_token, setup_store):
    response = client.put(
        "/api/v1/store-admin/settings/general",
        data={"name": "Updated Shop Name", "currency": "IRR"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Shop Name"
    setup_store.refresh_from_db()
    assert setup_store.name == "Updated Shop Name"


@pytest.mark.django_db
def test_tax_settings(client, admin_token, setup_store):
    response = client.put(
        "/api/v1/store-admin/settings/tax",
        data={"tax_enabled": True, "tax_percent": 9},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    setup_store.refresh_from_db()
    assert setup_store.tax_enabled is True


@pytest.mark.django_db
def test_seo_google_search_console(client, admin_token, setup_store):
    listed = client.get(
        "/api/v1/store-admin/settings",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert listed.status_code == 200
    seo = listed.json()["seo"]
    assert seo["verification_configured"] is False
    assert seo["sitemap_url"].endswith("/sitemap.xml")

    bad = client.put(
        "/api/v1/store-admin/settings/seo",
        data={"google_site_verification": "bad code!!"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert bad.status_code == 400

    saved = client.put(
        "/api/v1/store-admin/settings/seo",
        data={
            "google_site_verification": (
                '<meta name="google-site-verification" content="ApiToken_gsc999">'
            )
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert saved.status_code == 200
    data = saved.json()
    assert data["google_site_verification"] == "ApiToken_gsc999"
    assert data["verification_configured"] is True

    home = client.get("/", HTTP_HOST="localhost")
    assert 'content="ApiToken_gsc999"' in home.content.decode()


@pytest.mark.django_db
def test_list_customers(client, admin_token, customer_user):
    response = client.get(
        "/api/v1/store-admin/users",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1


@pytest.mark.django_db
def test_team_management(client, admin_token, setup_store, roles):
    response = client.post(
        "/api/v1/store-admin/team",
        data={"phone": "09125556666", "role": "products", "first_name": "Product", "last_name": "Manager"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    assert response.json()["role"] == "products"

    response = client.get(
        "/api/v1/store-admin/team",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.django_db
def test_products_api(client, admin_token, roles, setup_store):
    user = User.objects.create_user(phone="09127778888")
    StoreMembership.objects.create(
        user=user, store=setup_store, role=roles["products"], status=MembershipStatus.ACTIVE
    )
    token = JWTService().create_tokens(user.id, setup_store.id, "products", 1).access_token

    response = client.get(
        "/api/v1/store-admin/products/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_reports_summary(client, admin_token, roles, setup_store):
    user = User.objects.create_user(phone="09128889999")
    perm = Permission.objects.create(codename="reports.view", name="Reports", group="reports")
    reports_role = Role.objects.create(name="Reports", codename="reports", scope=RoleScope.STORE)
    reports_role.permissions.add(perm)
    StoreMembership.objects.create(user=user, store=setup_store, role=reports_role, status=MembershipStatus.ACTIVE)
    token = JWTService().create_tokens(user.id, setup_store.id, "reports", 1).access_token

    response = client.get(
        "/api/v1/store-admin/reports/summary",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    assert "new_customers" in response.json()
