"""Search and filter tests."""

import json

import pytest

from products.enums import ProductSortOrder, ProductStatus, ProductType
from products.models import (
    Brand,
    Category,
    Inventory,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductVariant,
)
from products.services.search import ProductSearchService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Search Shop", slug="search-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="search.local")
    return s


@pytest.fixture
def catalog(store):
    electronics = Category.objects.create(store=store, name="Electronics", slug="electronics")
    clothing = Category.objects.create(store=store, name="Clothing", slug="clothing")
    samsung = Brand.objects.create(store=store, name="Samsung", slug="samsung")
    nike = Brand.objects.create(store=store, name="Nike", slug="nike")

    phone = Product.objects.create(
        store=store, name="Galaxy Phone", slug="galaxy-phone", category=electronics, brand=samsung,
        status=ProductStatus.ACTIVE, base_price=40000000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=phone, quantity=5)

    shirt = Product.objects.create(
        store=store, name="Nike Shirt", slug="nike-shirt", category=clothing, brand=nike,
        status=ProductStatus.ACTIVE, base_price=500000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=shirt, quantity=0, track_inventory=True)

    cheap = Product.objects.create(
        store=store, name="Cheap Cable", slug="cheap-cable", category=electronics,
        status=ProductStatus.ACTIVE, base_price=100000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=cheap, quantity=20)

    color_attr = ProductAttribute.objects.create(store=store, name="Color", slug="color")
    red = ProductAttributeValue.objects.create(attribute=color_attr, value="Red", slug="red")
    blue = ProductAttributeValue.objects.create(attribute=color_attr, value="Blue", slug="blue")

    variable = Product.objects.create(
        store=store, name="Color Shirt", slug="color-shirt", category=clothing,
        status=ProductStatus.ACTIVE, base_price=600000, product_type=ProductType.VARIABLE,
    )
    v_red = ProductVariant.objects.create(product=variable, sku="CS-RED", price=600000)
    v_red.attributes.add(red)
    Inventory.objects.create(variant=v_red, product=variable, quantity=3)
    v_blue = ProductVariant.objects.create(product=variable, sku="CS-BLUE", price=650000)
    v_blue.attributes.add(blue)
    Inventory.objects.create(variant=v_blue, product=variable, quantity=0)

    return {
        "electronics": electronics,
        "samsung": samsung,
        "phone": phone,
        "shirt": shirt,
        "cheap": cheap,
        "variable": variable,
        "color_attr": color_attr,
        "red": red,
    }


@pytest.mark.django_db
def test_search_by_text(store, catalog):
    service = ProductSearchService()
    results = list(service.search(store, search="galaxy"))
    assert len(results) == 1
    assert results[0].slug == "galaxy-phone"


@pytest.mark.django_db
def test_filter_by_brand_and_price(store, catalog):
    service = ProductSearchService()
    results = list(service.search(store, brand_slug="samsung", min_price=1000000))
    assert len(results) == 1
    assert results[0].slug == "galaxy-phone"


@pytest.mark.django_db
def test_filter_in_stock(store, catalog):
    service = ProductSearchService()
    in_stock = list(service.search(store, in_stock=True))
    slugs = {p.slug for p in in_stock}
    assert "galaxy-phone" in slugs
    assert "cheap-cable" in slugs
    assert "nike-shirt" not in slugs


@pytest.mark.django_db
def test_sort_by_price(store, catalog):
    service = ProductSearchService()
    results = list(service.search(store, sort=ProductSortOrder.PRICE_ASC))
    prices = [int(p.base_price) for p in results]
    assert prices == sorted(prices)


@pytest.mark.django_db
def test_filter_by_attribute(store, catalog):
    service = ProductSearchService()
    results = list(service.search(store, attributes={"color": "red"}))
    assert len(results) == 1
    assert results[0].slug == "color-shirt"


@pytest.mark.django_db
def test_filter_options_api(client, store, catalog):
    response = client.get("/api/v1/products/filters", HTTP_HOST="search.local")
    assert response.status_code == 200
    data = response.json()
    assert len(data["brands"]) == 2
    assert data["price_range"]["max"] >= 40000000
    assert any(a["slug"] == "color" for a in data["attributes"])


@pytest.mark.django_db
def test_search_api_with_filters(client, store, catalog):
    response = client.get(
        "/api/v1/products/?search=shirt&min_price=400000&sort=price_desc",
        HTTP_HOST="search.local",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert all("shirt" in item["slug"] or "Shirt" in item["name"] for item in data["items"])


@pytest.mark.django_db
def test_storefront_search_page(client, store, catalog):
    response = client.get("/search/?q=galaxy", HTTP_HOST="search.local")
    assert response.status_code == 200
    content = response.content.decode()
    assert "product-catalog" in content
    assert "product-filters.js" in content


@pytest.mark.django_db
def test_storefront_category_with_filters(client, store, catalog):
    response = client.get("/products/electronics/", HTTP_HOST="search.local")
    assert response.status_code == 200
    assert "product-catalog" in response.content.decode()


@pytest.mark.django_db
def test_legacy_category_redirects_to_products(client, store, catalog):
    response = client.get("/category/electronics/", HTTP_HOST="search.local")
    assert response.status_code == 301
    assert response["Location"].endswith("/products/electronics/")


@pytest.mark.django_db
def test_parse_attributes_or_within_attr():
    parsed = ProductSearchService.parse_attributes("color:red,color:blue,size:m")
    assert parsed == {"color": ["red", "blue"], "size": ["m"]}


@pytest.mark.django_db
def test_filter_options_scoped_to_category(store, catalog):
    service = ProductSearchService()
    clothing = service.get_filter_options(store, "clothing")
    assert any(a["slug"] == "color" for a in clothing["attributes"])
    electronics = service.get_filter_options(store, "electronics")
    # Electronics catalog has no variants with color in fixture
    assert not any(a["slug"] == "color" for a in electronics["attributes"])