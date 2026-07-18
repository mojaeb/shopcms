"""Tests for tenant models."""

import pytest

from tenants.models import Domain, Store, Theme


@pytest.fixture
def default_theme(db):
    return Theme.objects.create(
        name="Default",
        slug="default",
        directory="default",
        is_default=True,
    )


@pytest.fixture
def modern_theme(db):
    return Theme.objects.create(
        name="Modern",
        slug="modern",
        directory="modern",
    )


@pytest.fixture
def store(db, default_theme, modern_theme):
    return Store.objects.create(
        name="Test Shop",
        slug="test-shop",
        store_type="physical",
        theme=modern_theme,
        default_theme=default_theme,
        status="active",
    )


@pytest.mark.django_db
def test_store_effective_theme(store, modern_theme):
    assert store.effective_theme == modern_theme
    assert store.effective_theme_slug == "modern"


@pytest.mark.django_db
def test_store_fallback_theme(store, default_theme, modern_theme):
    store.theme = None
    store.save()
    assert store.effective_theme == default_theme
    assert store.effective_theme_slug == "default"


@pytest.mark.django_db
def test_domain_primary_unique(store):
    d1 = Domain.objects.create(store=store, domain="shop1.com", is_primary=True)
    d2 = Domain.objects.create(store=store, domain="shop2.com", is_primary=True)
    d1.refresh_from_db()
    assert d2.is_primary is True
    assert d1.is_primary is False


@pytest.mark.django_db
def test_theme_default_unique(db):
    t1 = Theme.objects.create(name="T1", slug="t1", directory="t1", is_default=True)
    t2 = Theme.objects.create(name="T2", slug="t2", directory="t2", is_default=True)
    t1.refresh_from_db()
    assert t2.is_default is True
    assert t1.is_default is False
