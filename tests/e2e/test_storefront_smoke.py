"""Storefront smoke tests."""

import pytest
from django.test import Client

from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="Smoke Shop", slug="smoke-shop", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="smoke.local")
    return store


@pytest.mark.django_db
def test_storefront_home(client: Client, store):
    response = client.get("/", HTTP_HOST="smoke.local")
    assert response.status_code in (200, 302)


@pytest.mark.django_db
def test_health_and_metrics(client: Client):
    live = client.get("/api/v1/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    metrics = client.get("/api/v1/health/metrics")
    assert metrics.status_code == 200
    assert "stores_total" in metrics.json()
