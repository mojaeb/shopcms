"""Products tests."""

import json
from decimal import Decimal

import pytest

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from products.enums import ProductStatus, ProductType
from products.models import Brand, Category, Inventory, Product, ProductImage
from products.services.product import ProductService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Product Shop", slug="product-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="products.local")
    return s


@pytest.fixture
def product_data(store):
    category = Category.objects.create(store=store, name="Electronics", slug="electronics")
    brand = Brand.objects.create(store=store, name="Samsung", slug="samsung")
    product = Product.objects.create(
        store=store,
        name="Galaxy S24",
        slug="galaxy-s24",
        category=category,
        brand=brand,
        product_type=ProductType.SIMPLE,
        status=ProductStatus.ACTIVE,
        base_price=45000000,
        short_description="Smartphone",
        description="Sample product",
    )
    ProductImage.objects.create(
        product=product,
        image="https://example.com/s24.jpg",
        is_primary=True,
    )
    Inventory.objects.create(product=product, quantity=10)
    return {"category": category, "brand": brand, "product": product}


@pytest.fixture
def products_token(store):
    perm = Permission.objects.create(codename="products.view", name="Products", group="products")
    role = Role.objects.create(name="Products", codename="products", scope=RoleScope.STORE)
    role.permissions.add(perm)
    user = User.objects.create_user(phone="09121112233")
    m = StoreMembership.objects.create(user=user, store=store, role=role, status=MembershipStatus.ACTIVE)
    return JWTService().create_tokens(user.id, store.id, "products", m.id).access_token


@pytest.mark.django_db
def test_product_service_list(store, product_data):
    service = ProductService()
    products = list(service.list_products(store))
    assert len(products) == 1
    assert products[0].slug == "galaxy-s24"


@pytest.mark.django_db
def test_product_service_detail(store, product_data):
    service = ProductService()
    product = service.get_product(store, "galaxy-s24")
    assert product is not None
    detail = service.serialize_product_detail(product)
    assert detail["name"] == "Galaxy S24"
    assert detail["in_stock"] is True
    assert detail["available"] == 10
    assert len(detail["images"]) == 1


@pytest.mark.django_db
def test_product_service_category_filter(store, product_data):
    service = ProductService()
    products = list(service.list_products(store, category_slug="electronics"))
    assert len(products) == 1
    products = list(service.list_products(store, category_slug="missing"))
    assert len(products) == 0


@pytest.mark.django_db
def test_products_public_api(client, store, product_data):
    response = client.get("/api/v1/products/", HTTP_HOST="products.local")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["items"][0]["slug"] == "galaxy-s24"

    response = client.get("/api/v1/products/galaxy-s24", HTTP_HOST="products.local")
    assert response.status_code == 200
    assert response.json()["name"] == "Galaxy S24"

    response = client.get("/api/v1/products/categories/list", HTTP_HOST="products.local")
    assert response.status_code == 200
    assert response.json()[0]["slug"] == "electronics"


@pytest.mark.django_db
def test_product_list_paginates_and_caches(client, store):
    from django.core.cache import cache

    from core.cache import cache_manager
    from core.cache.keys import product_list
    from products.enums import ProductStatus

    for i in range(25):
        Product.objects.create(
            store=store,
            name=f"Item {i}",
            slug=f"item-{i}",
            status=ProductStatus.ACTIVE,
            base_price=1000 + i,
        )

    response = client.get("/api/v1/products/?page=1&page_size=20", HTTP_HOST="products.local")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 25
    assert len(data["items"]) == 20

    page2 = client.get("/api/v1/products/?page=2&page_size=20", HTTP_HOST="products.local")
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 5

    # Second hit should come from cache (tamper cache and re-fetch)
    params_hash = cache_manager.hash_params(
        {
            "search": "",
            "category": None,
            "brand_slugs": [],
            "min_price": None,
            "max_price": None,
            "attributes": {},
            "tag": None,
            "in_stock": None,
            "featured": None,
            "sort": "newest",
            "page": 1,
            "page_size": 20,
        }
    )
    key = product_list(store.id, params_hash)
    cache.set(key, {"items": [{"slug": "from-cache"}], "count": 1}, 60)
    cached = client.get("/api/v1/products/?page=1&page_size=20", HTTP_HOST="products.local")
    assert cached.json()["items"][0]["slug"] == "from-cache"


@pytest.mark.django_db
def test_product_detail_cache_invalidates_on_save(client, store, product_data):
    from django.core.cache import cache

    from core.cache.keys import product_detail

    first = client.get("/api/v1/products/galaxy-s24", HTTP_HOST="products.local")
    assert first.status_code == 200
    assert first.json()["name"] == "Galaxy S24"

    key = product_detail(store.id, "galaxy-s24")
    cache.set(key, {"name": "Cached Name", "slug": "galaxy-s24"}, 60)
    second = client.get("/api/v1/products/galaxy-s24", HTTP_HOST="products.local")
    assert second.json()["name"] == "Cached Name"

    product = product_data["product"]
    product.name = "Galaxy S24 Ultra"
    product.save()

    third = client.get("/api/v1/products/galaxy-s24", HTTP_HOST="products.local")
    assert third.json()["name"] == "Galaxy S24 Ultra"


@pytest.mark.django_db
def test_products_admin_api(client, store, products_token):
    response = client.post(
        "/api/v1/store-admin/products/categories",
        data=json.dumps({"name": "Phones", "slug": "phones"}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {products_token}",
        HTTP_HOST="products.local",
    )
    assert response.status_code == 200
    category_id = response.json()["id"]

    response = client.post(
        "/api/v1/store-admin/products/",
        data=json.dumps({
            "name": "Test Phone",
            "slug": "test-phone",
            "status": ProductStatus.ACTIVE,
            "base_price": 1000000,
            "category_id": category_id,
            "initial_stock": 5,
        }),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {products_token}",
        HTTP_HOST="products.local",
    )
    assert response.status_code == 200
    product_id = response.json()["id"]

    response = client.get(
        f"/api/v1/store-admin/products/{product_id}",
        HTTP_AUTHORIZATION=f"Bearer {products_token}",
        HTTP_HOST="products.local",
    )
    assert response.status_code == 200
    assert response.json()["slug"] == "test-phone"
    assert response.json()["available"] == 5


@pytest.mark.django_db
def test_products_admin_variable_create_update(client, store, products_token):
    from products.models import ProductVariant

    # create attributes
    response = client.post(
        "/api/v1/store-admin/products/attributes",
        data=json.dumps({
            "name": "رنگ",
            "slug": "color",
            "display_type": "color",
            "values": [
                {"value": "قرمز", "slug": "red", "color_code": "#ff0000"},
                {"value": "آبی", "slug": "blue", "color_code": "#0000ff"},
            ],
        }),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {products_token}",
        HTTP_HOST="products.local",
    )
    assert response.status_code == 200, response.content
    attr = response.json()
    red_id = attr["values"][0]["id"]
    blue_id = attr["values"][1]["id"]

    response = client.post(
        "/api/v1/store-admin/products/",
        data=json.dumps({
            "name": "تیشرت رنگی",
            "slug": "color-tee",
            "product_type": ProductType.VARIABLE,
            "status": ProductStatus.ACTIVE,
            "base_price": 500000,
            "images": [
                {"image": "https://example.com/tee.jpg", "is_primary": True},
            ],
            "tags": ["summer", "new"],
            "variants": [
                {
                    "sku": "TEE-RED",
                    "price": 500000,
                    "stock": 4,
                    "attribute_value_ids": [red_id],
                },
                {
                    "sku": "TEE-BLUE",
                    "price": 520000,
                    "stock": 2,
                    "attribute_value_ids": [blue_id],
                },
            ],
            "meta_title": "تیشرت",
        }),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {products_token}",
        HTTP_HOST="products.local",
    )
    assert response.status_code == 200, response.content
    created = response.json()
    assert created["product_type"] == ProductType.VARIABLE
    assert len(created["variants"]) == 2
    assert created["available"] == 6
    assert len(created["images"]) == 1
    product_id = created["id"]
    red_variant_id = created["variants"][0]["id"]

    response = client.put(
        f"/api/v1/store-admin/products/{product_id}",
        data=json.dumps({
            "name": "تیشرت رنگی ۲",
            "variants": [
                {
                    "id": red_variant_id,
                    "sku": "TEE-RED",
                    "price": 510000,
                    "stock": 10,
                    "attribute_value_ids": [red_id],
                    "is_active": True,
                },
            ],
        }),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {products_token}",
        HTTP_HOST="products.local",
    )
    assert response.status_code == 200, response.content
    updated = response.json()
    assert updated["name"] == "تیشرت رنگی ۲"
    assert len(updated["variants"]) == 1
    assert updated["variants"][0]["stock"] == 10
    assert updated["available"] == 10
    assert ProductVariant.objects.filter(product_id=product_id).count() == 1


@pytest.mark.django_db
def test_products_admin_simple_stock_update(client, store, products_token, product_data):
    product = product_data["product"]
    response = client.put(
        f"/api/v1/store-admin/products/{product.id}",
        data=json.dumps({
            "stock": 25,
            "description": "updated desc",
            "sku": "S24-NEW",
        }),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {products_token}",
        HTTP_HOST="products.local",
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["stock"] == 25
    assert data["sku"] == "S24-NEW"
    assert data["description"] == "updated desc"


@pytest.mark.django_db
def test_storefront_product_page(client, store, product_data):
    response = client.get("/product/galaxy-s24/", HTTP_HOST="products.local")
    assert response.status_code == 200
    assert "Galaxy S24" in response.content.decode()


@pytest.mark.django_db
def test_storefront_category_page(client, store, product_data):
    response = client.get("/products/electronics/", HTTP_HOST="products.local")
    assert response.status_code == 200
    assert "galaxy-s24" in response.content.decode() or "Galaxy S24" in response.content.decode()


@pytest.mark.django_db
def test_product_weight_kg_default_and_set(store):
    product = Product.objects.create(
        store=store,
        name="Scale",
        slug="scale",
        product_type=ProductType.SIMPLE,
        status=ProductStatus.ACTIVE,
        base_price=10000,
    )
    assert product.weight_kg == Decimal("0.5")
    product.weight_kg = Decimal("2.250")
    product.save(update_fields=["weight_kg"])
    product.refresh_from_db()
    assert product.weight_kg == Decimal("2.250")


@pytest.mark.django_db
def test_variant_weight_kg_nullable(store, product_data):
    from products.models import ProductVariant

    product = product_data["product"]
    variant = ProductVariant.objects.create(product=product, price=1000)
    assert variant.weight_kg is None
    variant.weight_kg = Decimal("1.100")
    variant.save(update_fields=["weight_kg"])
    variant.refresh_from_db()
    assert variant.weight_kg == Decimal("1.100")
