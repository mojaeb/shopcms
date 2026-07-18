"""Wishlist tests."""

import json

import pytest

from accounts.models import User
from accounts.services.jwt import JWTService
from products.enums import ProductStatus, ProductType
from products.models import Inventory, Product
from tenants.models import Domain, Plugin, Store, StorePlugin, Theme
from wishlists.models import WishlistItem
from wishlists.services.wishlist import WishlistError, WishlistService


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Wish Shop", slug="wish-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="wish.local")
    plugin, _ = Plugin.objects.get_or_create(codename="wishlist", defaults={"name": "Wishlist", "is_active": True})
    StorePlugin.objects.create(store=s, plugin=plugin, is_enabled=True)
    return s


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="09123334466", phone_verified=True)


@pytest.fixture
def product(store):
    p = Product.objects.create(
        store=store, name="Wish Product", slug="wish-product",
        status=ProductStatus.ACTIVE, base_price=800000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=p, quantity=5)
    return p


@pytest.fixture
def auth_headers(user, store):
    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "wish.local"}


@pytest.mark.django_db
def test_add_and_list_wishlist(store, user, product):
    service = WishlistService()
    service.add_item(user, store, "wish-product")
    items = service.list_items(user, store)
    assert items.count() == 1
    assert items.first().product.slug == "wish-product"


@pytest.mark.django_db
def test_toggle_wishlist(store, user, product):
    service = WishlistService()
    result = service.toggle_item(user, store, "wish-product")
    assert result["in_wishlist"] is True
    result = service.toggle_item(user, store, "wish-product")
    assert result["in_wishlist"] is False
    assert WishlistItem.objects.count() == 0


@pytest.mark.django_db
def test_wishlist_requires_plugin(store, user, product):
    StorePlugin.objects.filter(store=store).update(is_enabled=False)
    with pytest.raises(WishlistError):
        WishlistService().add_item(user, store, "wish-product")


@pytest.mark.django_db
def test_wishlist_api(client, store, user, auth_headers, product):
    response = client.post(
        "/api/v1/wishlist/add",
        data=json.dumps({"product_slug": "wish-product"}),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = client.get("/api/v1/wishlist/", **auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["slug"] == "wish-product"


@pytest.mark.django_db
def test_wishlist_toggle_api(client, store, user, auth_headers, product):
    response = client.post(
        "/api/v1/wishlist/toggle",
        data=json.dumps({"product_slug": "wish-product"}),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["in_wishlist"] is True

    response = client.get("/api/v1/wishlist/check/wish-product", **auth_headers)
    assert response.json()["in_wishlist"] is True


@pytest.mark.django_db
def test_wishlist_requires_auth(client, store, product):
    response = client.get("/api/v1/wishlist/", HTTP_HOST="wish.local")
    assert response.status_code == 401


@pytest.mark.django_db
def test_storefront_wishlist_page(client, store):
    response = client.get("/wishlist/", HTTP_HOST="wish.local")
    assert response.status_code == 200
    assert "wishlist-page" in response.content.decode()
