"""Tests for bulk import/export shipping prices API and locations endpoint."""

import json

import pytest

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from shipping.enums import CalculationMode, ShippingProviderType
from shipping.models import ShippingMethod, ShippingPrice, ShippingZone
from tenants.models import Domain, Store, Theme


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default-bulk", directory="default", is_default=False)
    s = Store.objects.create(name="Bulk Shop", slug="bulk-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="bulk.local")
    return s


@pytest.fixture
def staff_headers(db, store):
    role = Role.objects.create(name="Admin", codename="store_admin", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="settings.manage", name="Manage Settings", group="settings")
    role.permissions.add(perm)
    user = User.objects.create_user(phone="09120000001", is_staff=True)
    membership = StoreMembership.objects.create(
        user=user, store=store, role=role, status=MembershipStatus.ACTIVE, is_primary=True,
    )
    token = JWTService().create_tokens(user.id, store.id, "store_admin", membership.id).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "bulk.local"}


@pytest.fixture
def method(store):
    zone = ShippingZone.objects.create(store=store, name="All", is_active=True)
    return ShippingMethod.objects.create(
        store=store, zone=zone, name="Post", slug="post-bulk",
        provider=ShippingProviderType.POST,
        calculation_mode=CalculationMode.WEIGHT,
        config={"fixed_price": 50000},
    )


TWO_ROWS = [
    {"from_city": "مشهد", "to_city": "تهران", "zone_tier": "", "weight_min_kg": 0, "weight_max_kg": 5, "price": 100000, "extra_per_kg": 0},
    {"from_city": "مشهد", "to_city": "تهران", "zone_tier": "", "weight_min_kg": 5, "weight_max_kg": 10, "price": 150000, "extra_per_kg": 5000},
]


# ──────────────────────────────────────────────────────────────────────────────
# Tests — bulk import
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_bulk_import_creates_rows(client, method, staff_headers):
    response = client.post(
        f"/api/v1/store-admin/shipping/methods/{method.id}/prices/bulk",
        data=json.dumps({"rows": TWO_ROWS}),
        content_type="application/json",
        **staff_headers,
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["created"] == 2
    assert data["updated"] == 0
    assert ShippingPrice.objects.filter(method=method).count() == 2


@pytest.mark.django_db
def test_bulk_import_upsert_no_duplicate(client, method, staff_headers):
    """ارسال مجدد همان ردیف‌ها باید update کند نه رکورد جدید بسازد."""
    for _ in range(2):
        response = client.post(
            f"/api/v1/store-admin/shipping/methods/{method.id}/prices/bulk",
            data=json.dumps({"rows": TWO_ROWS}),
            content_type="application/json",
            **staff_headers,
        )
        assert response.status_code == 200

    assert ShippingPrice.objects.filter(method=method).count() == 2
    data = response.json()
    assert data["created"] == 0
    assert data["updated"] == 2


@pytest.mark.django_db
def test_bulk_import_invalid_weight_range(client, method, staff_headers):
    """weight_min >= weight_max باید با 400 و پیام فارسی رد شود."""
    bad_rows = [
        {"from_city": "", "to_city": "تهران", "zone_tier": "", "weight_min_kg": 10, "weight_max_kg": 5, "price": 80000, "extra_per_kg": 0},
    ]
    response = client.post(
        f"/api/v1/store-admin/shipping/methods/{method.id}/prices/bulk",
        data=json.dumps({"rows": bad_rows}),
        content_type="application/json",
        **staff_headers,
    )
    assert response.status_code == 400
    body = response.json()
    msg = body.get("detail", "")
    assert "وزن" in msg


@pytest.mark.django_db
def test_bulk_import_overlap_warning(client, method, staff_headers):
    """ردیف‌های با بازه‌ی وزنی هم‌پوشان: import موفق اما warnings برمی‌گرداند."""
    overlap_rows = [
        {"from_city": "مشهد", "to_city": "تهران", "zone_tier": "", "weight_min_kg": 0, "weight_max_kg": 8, "price": 100000, "extra_per_kg": 0},
        {"from_city": "مشهد", "to_city": "تهران", "zone_tier": "", "weight_min_kg": 5, "weight_max_kg": 15, "price": 140000, "extra_per_kg": 0},
    ]
    response = client.post(
        f"/api/v1/store-admin/shipping/methods/{method.id}/prices/bulk",
        data=json.dumps({"rows": overlap_rows}),
        content_type="application/json",
        **staff_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["warnings"]) > 0
    assert ShippingPrice.objects.filter(method=method).count() == 2


@pytest.mark.django_db
def test_bulk_import_replace_all(client, method, staff_headers):
    """replace_all=True باید ردیف‌های قدیمی را حذف و فقط ردیف‌های جدید بگذارد."""
    # ابتدا یک ردیف قدیمی می‌سازیم
    ShippingPrice.objects.create(method=method, from_city="قدیمی", to_city="قدیمی", price=999)

    response = client.post(
        f"/api/v1/store-admin/shipping/methods/{method.id}/prices/bulk",
        data=json.dumps({"rows": TWO_ROWS, "replace_all": True}),
        content_type="application/json",
        **staff_headers,
    )
    assert response.status_code == 200
    assert ShippingPrice.objects.filter(method=method).count() == 2
    assert not ShippingPrice.objects.filter(method=method, from_city="قدیمی").exists()


# ──────────────────────────────────────────────────────────────────────────────
# Tests — export
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_export_prices(client, method, staff_headers):
    ShippingPrice.objects.create(method=method, from_city="مشهد", to_city="تهران", price=120000)
    ShippingPrice.objects.create(method=method, from_city="مشهد", to_city="اصفهان", price=90000)

    response = client.get(
        f"/api/v1/store-admin/shipping/methods/{method.id}/prices/export",
        **staff_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["method_id"] == method.id
    assert data["total"] == 2
    assert len(data["rows"]) == 2
    assert all("price" in r for r in data["rows"])


# ──────────────────────────────────────────────────────────────────────────────
# Tests — locations
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_locations_returns_provinces(client, staff_headers):
    response = client.get("/api/v1/store-admin/shipping/locations", **staff_headers)
    assert response.status_code == 200
    data = response.json()
    provinces = data["provinces"]
    assert isinstance(provinces, list)
    assert len(provinces) >= 30  # ۳۱ استان ایران
    assert "تهران" in provinces
    assert "خراسان رضوی" in provinces
    assert data["zone_tiers"]  # لیست tier ها خالی نباشد
