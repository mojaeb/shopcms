"""Tests for theme engine."""

import pytest
from django.template import TemplateDoesNotExist
from django.template.loader import get_template

from tenants.context import set_current_store
from tenants.models import Domain, Store, Theme
from tenants.services.theme import ThemeResolver
from tenants.theme.engine import ThemeEngine
from tenants.theme.pages import STOREFRONT_PAGES


@pytest.fixture
def themes(db):
    default = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    modern = Theme.objects.create(name="Modern", slug="modern", directory="modern")
    minimal = Theme.objects.create(name="Minimal", slug="minimal", directory="minimal")
    return {"default": default, "modern": modern, "minimal": minimal}


@pytest.fixture
def modern_store(db, themes):
    store = Store.objects.create(
        name="Modern Shop", slug="modern-shop", theme=themes["modern"],
        default_theme=themes["default"], status="active",
    )
    Domain.objects.create(store=store, domain="modern.local")
    return store


@pytest.fixture
def minimal_store(db, themes):
    store = Store.objects.create(
        name="Minimal Shop", slug="minimal-shop", theme=themes["minimal"],
        default_theme=themes["default"], status="active",
    )
    Domain.objects.create(store=store, domain="minimal.local")
    return store


@pytest.mark.django_db
def test_resolver_fallback(modern_store):
    resolver = ThemeResolver()
    assert resolver.resolve_template_name("home.html", modern_store) == "themes/modern/home.html"
    assert resolver.resolve_template_name("cart.html", modern_store) == "themes/default/cart.html"
    assert resolver.resolve_template_name("partials/header.html", modern_store) == "themes/default/partials/header.html"


@pytest.mark.django_db
def test_theme_engine_info(modern_store):
    engine = ThemeEngine()
    info = engine.get_theme_info(modern_store)
    assert info["theme_slug"] == "modern"
    assert "home.html" in info["templates"]
    assert "cart.html" in info["inherited"]


@pytest.mark.django_db
def test_all_pages_exist_in_default():
    resolver = ThemeResolver()
    for page_key, template in STOREFRONT_PAGES.items():
        path = resolver.resolve_template_name(template)
        full = resolver.themes_dir.parent / path if not str(path).startswith("themes") else resolver.themes_dir.parent.parent / path
        from django.conf import settings
        assert (settings.BASE_DIR / path).exists(), f"Missing template for {page_key}: {path}"


@pytest.mark.django_db
def test_theme_loader_resolves_partial(modern_store):
    set_current_store(modern_store)
    template = get_template("partials/header.html")
    assert template is not None
    set_current_store(None)


@pytest.mark.django_db
def test_storefront_pages(client, modern_store):
    from products.enums import ProductStatus, ProductType
    from products.models import Product

    Product.objects.create(
        store=modern_store,
        name="Test Item",
        slug="test-item",
        product_type=ProductType.SIMPLE,
        status=ProductStatus.ACTIVE,
        base_price=1000,
    )

    pages = ["/", "/cart/", "/blog/", "/dashboard/", "/product/test-item/"]
    for url in pages:
        response = client.get(url, HTTP_HOST="modern.local")
        assert response.status_code == 200, f"Failed for {url}"

    checkout = client.get("/checkout/", HTTP_HOST="modern.local")
    assert checkout.status_code == 302
    assert checkout["Location"].startswith("/login/?next=")
    assert "/checkout/" in checkout["Location"]


@pytest.mark.django_db
def test_modern_home_content(client, modern_store):
    response = client.get("/", HTTP_HOST="modern.local")
    content = response.content.decode()
    assert response.status_code == 200
    assert "vg-home" in content
    assert "Modern Shop" in content
    assert "theme-modern" in content


@pytest.mark.django_db
def test_minimal_home_content(client, minimal_store):
    response = client.get("/", HTTP_HOST="minimal.local")
    content = response.content.decode()
    assert response.status_code == 200
    assert "Minimal Shop" in content
    assert "theme-minimal" in content


@pytest.mark.django_db
def test_cart_uses_default_theme(client, modern_store):
    response = client.get("/cart/", HTTP_HOST="modern.local")
    content = response.content.decode()
    assert "سبد خرید" in content
    assert "cart-page" in content


@pytest.mark.django_db
def test_theme_api(client, modern_store):
    response = client.get("/api/v1/store/theme/info", HTTP_HOST="modern.local")
    assert response.status_code == 200
    data = response.json()
    assert data["theme_slug"] == "modern"
    assert "pages" in data
