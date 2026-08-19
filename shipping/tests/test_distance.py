"""Tests for shipping distance module and geo helpers."""

from decimal import Decimal
from unittest.mock import patch

import pytest

from core.utils.geo import is_iran_coordinate
from shipping.distance import haversine_km, real_distance_km
from shipping.providers.base import ShippingContext
from shipping.services.shipping import ShippingService
from tenants.models import Domain, Store, Theme


# ── haversine_km ──────────────────────────────────────────────────────────────

def test_haversine_tehran_mashhad():
    """تهران (35.6892, 51.3890) → مشهد (36.2972, 59.6067): خط مستقیم ~۷۴۱ کیلومتر."""
    result = haversine_km(35.6892, 51.3890, 36.2972, 59.6067)
    assert isinstance(result, Decimal)
    assert 700 < float(result) < 800, f"expected ~741 km, got {result}"


def test_haversine_same_point():
    result = haversine_km(35.0, 51.0, 35.0, 51.0)
    assert result == Decimal("0.0")


def test_haversine_returns_decimal():
    result = haversine_km(35.0, 51.0, 36.0, 52.0)
    assert isinstance(result, Decimal)


# ── is_iran_coordinate ────────────────────────────────────────────────────────

def test_iran_coordinate_tehran():
    assert is_iran_coordinate(35.6892, 51.3890) is True


def test_iran_coordinate_mashhad():
    assert is_iran_coordinate(36.2972, 59.6067) is True


def test_iran_coordinate_outside_north():
    # شمال قفقاز
    assert is_iran_coordinate(42.0, 51.0) is False


def test_iran_coordinate_outside_west():
    # غرب ترکیه
    assert is_iran_coordinate(35.0, 30.0) is False


def test_iran_coordinate_outside_east():
    # پاکستان شرقی
    assert is_iran_coordinate(30.0, 70.0) is False


def test_iran_coordinate_outside_south():
    # اقیانوس هند
    assert is_iran_coordinate(20.0, 55.0) is False


# ── real_distance_km (fallback) ───────────────────────────────────────────────

def test_real_distance_no_api_key_uses_haversine():
    """بدون api_key باید به haversine fallback کند."""
    result = real_distance_km(35.6892, 51.3890, 36.2972, 59.6067, api_key="")
    expected = haversine_km(35.6892, 51.3890, 36.2972, 59.6067)
    assert result == expected


def test_real_distance_caches_result():
    from django.core.cache import cache
    cache.clear()
    r1 = real_distance_km(35.0, 51.0, 36.0, 52.0, api_key="", store_id=99)
    r2 = real_distance_km(35.0, 51.0, 36.0, 52.0, api_key="", store_id=99)
    assert r1 == r2


# ── build_context با مختصات ───────────────────────────────────────────────────

@pytest.fixture
def store_with_coords(db):
    theme = Theme.objects.create(name="Default", slug="default2", directory="default", is_default=False)
    s = Store.objects.create(
        name="Geo Shop", slug="geo-shop", default_theme=theme, status="active",
        origin_latitude=Decimal("35.6892"),
        origin_longitude=Decimal("51.3890"),
    )
    Domain.objects.create(store=s, domain="geo.local")
    return s


@pytest.fixture
def store_no_coords(db):
    theme = Theme.objects.create(name="Default NC", slug="default-nc", directory="default", is_default=False)
    s = Store.objects.create(name="No Coord Shop", slug="no-coord-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="nocoord.local")
    return s


@pytest.mark.django_db
def test_build_context_with_coordinates_sets_distance(store_with_coords):
    svc = ShippingService()
    ctx = svc.build_context(
        store_with_coords, "خراسان رضوی", "مشهد",
        dest_lat=36.2972, dest_lng=59.6067,
    )
    assert ctx.distance_km is not None
    assert 700 < float(ctx.distance_km) < 800


@pytest.mark.django_db
def test_build_context_without_coordinates_distance_none(store_with_coords):
    svc = ShippingService()
    ctx = svc.build_context(store_with_coords, "تهران", "تهران")
    assert ctx.distance_km is None


@pytest.mark.django_db
def test_build_context_no_store_origin_distance_none(store_no_coords):
    svc = ShippingService()
    ctx = svc.build_context(
        store_no_coords, "خراسان رضوی", "مشهد",
        dest_lat=36.2972, dest_lng=59.6067,
    )
    assert ctx.distance_km is None


@pytest.mark.django_db
def test_build_context_outside_iran_distance_none(store_with_coords):
    svc = ShippingService()
    ctx = svc.build_context(
        store_with_coords, "تهران", "تهران",
        dest_lat=48.8566, dest_lng=2.3522,  # پاریس
    )
    assert ctx.distance_km is None
