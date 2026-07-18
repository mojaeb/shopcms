"""Tests for store resolution and middleware."""

import pytest
from django.test import Client, RequestFactory

from tenants.middleware import TenantMiddleware
from tenants.models import Domain, Store, Theme
from tenants.services.store import StoreNotFoundError, StoreService
from tenants.services.theme import ThemeResolver


@pytest.fixture
def setup_store(db):
    default = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    modern = Theme.objects.create(name="Modern", slug="modern", directory="modern")
    store = Store.objects.create(
        name="Shop One",
        slug="shop1",
        theme=modern,
        default_theme=default,
        status="active",
    )
    Domain.objects.create(store=store, domain="shop1.local", is_primary=True)
    Domain.objects.create(store=store, domain="localhost")
    return store


@pytest.mark.django_db
def test_resolve_by_host(setup_store):
    service = StoreService()
    store = service.resolve_by_host("shop1.local")
    assert store.slug == "shop1"


@pytest.mark.django_db
def test_resolve_by_host_not_found():
    service = StoreService()
    with pytest.raises(StoreNotFoundError):
        service.resolve_by_host("unknown.com")


@pytest.mark.django_db
def test_theme_resolver_fallback(setup_store):
    resolver = ThemeResolver()
    assert resolver.resolve_template_name("home.html", setup_store) == "themes/modern/home.html"
    assert resolver.resolve_template_name("product.html", setup_store) == "themes/default/product.html"


@pytest.mark.django_db
def test_middleware_sets_store(setup_store):
    factory = RequestFactory()
    request = factory.get("/", HTTP_HOST="shop1.local")

    def get_response(req):
        assert req.store.slug == "shop1"
        assert req.theme_slug == "modern"
        from django.http import HttpResponse
        return HttpResponse("ok")

    middleware = TenantMiddleware(get_response)
    response = middleware(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_storefront_home(client, setup_store):
    response = client.get("/", HTTP_HOST="shop1.local")
    assert response.status_code == 200
    assert "Shop One" in response.content.decode()
    assert "تم مدرن" in response.content.decode()


@pytest.mark.django_db
def test_store_api_current(client, setup_store):
    response = client.get("/api/v1/store/current", HTTP_HOST="shop1.local")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "shop1"
    assert data["theme_slug"] == "modern"
