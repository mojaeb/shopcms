"""Cart tests."""

import json

import pytest

from accounts.models import User
from accounts.services.jwt import JWTService
from carts.enums import DiscountType
from carts.models import Cart, Coupon
from carts.services.cart import CartError, CartService
from products.enums import ProductStatus, ProductType
from products.models import Inventory, Product
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Cart Shop", slug="cart-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="cart.local")
    return s


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="09121112233", phone_verified=True)


@pytest.fixture
def auth_headers(user, store):
    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "cart.local"}


@pytest.fixture
def product(store):
    p = Product.objects.create(
        store=store,
        name="Test Product",
        slug="test-product",
        status=ProductStatus.ACTIVE,
        base_price=1000000,
        product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=p, quantity=10)
    return p


@pytest.fixture
def coupon(store):
    from tenants.models import Plugin, StorePlugin

    plugin, _ = Plugin.objects.get_or_create(codename="coupon", defaults={"name": "Coupons", "is_active": True})
    StorePlugin.objects.get_or_create(store=store, plugin=plugin, defaults={"is_enabled": True})
    return Coupon.objects.create(
        store=store,
        code="SAVE10",
        discount_type=DiscountType.PERCENTAGE,
        value=10,
        min_order_amount=0,
        is_active=True,
    )


@pytest.mark.django_db
def test_add_requires_auth(client, store, product):
    response = client.post(
        "/api/v1/cart/add",
        data=json.dumps({"product_slug": "test-product", "quantity": 1}),
        content_type="application/json",
        HTTP_HOST="cart.local",
    )
    assert response.status_code == 401
    assert "ورود" in response.json()["detail"]


@pytest.mark.django_db
def test_add_and_serialize_cart(client, store, product, auth_headers):
    response = client.post(
        "/api/v1/cart/add",
        data=json.dumps({"product_slug": "test-product", "quantity": 2}),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["item_count"] == 2
    assert data["subtotal"] == "2000000"
    assert len(data["items"]) == 1


@pytest.mark.django_db
def test_add_with_django_session(client, store, product, user):
    """Storefront session login (no Bearer) can still add to cart."""
    client.force_login(user)
    response = client.post(
        "/api/v1/cart/add",
        data=json.dumps({"product_slug": "test-product", "quantity": 1}),
        content_type="application/json",
        HTTP_HOST="cart.local",
    )
    assert response.status_code == 200
    assert response.json()["item_count"] == 1


@pytest.mark.django_db
def test_update_cart_quantity(client, store, product, auth_headers):
    client.post(
        "/api/v1/cart/add",
        data=json.dumps({"product_slug": "test-product", "quantity": 1}),
        content_type="application/json",
        **auth_headers,
    )
    cart_data = client.get("/api/v1/cart/", **auth_headers).json()
    item_id = cart_data["items"][0]["id"]

    response = client.post(
        "/api/v1/cart/update",
        data=json.dumps({"item_id": item_id, "quantity": 3}),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["item_count"] == 3


@pytest.mark.django_db
def test_remove_cart_item(client, store, product, auth_headers):
    client.post(
        "/api/v1/cart/add",
        data=json.dumps({"product_slug": "test-product", "quantity": 1}),
        content_type="application/json",
        **auth_headers,
    )
    item_id = client.get("/api/v1/cart/", **auth_headers).json()["items"][0]["id"]

    response = client.post(
        "/api/v1/cart/remove",
        data=json.dumps({"item_id": item_id}),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["item_count"] == 0


@pytest.mark.django_db
def test_apply_coupon(client, store, product, coupon):
    service = CartService()
    cart = Cart.objects.create(store=store, session_key="cp-session")
    service.add_item(cart, "test-product", quantity=1)

    class R:
        META = {}
        session = type("S", (), {"session_key": "cp-session"})()

    cart = service.apply_coupon(cart, "SAVE10")
    totals = service.calculate_totals(cart)
    assert totals["discount"] == 100000
    assert totals["total"] == 900000


@pytest.mark.django_db
def test_insufficient_stock(store, product):
    service = CartService()
    cart = Cart.objects.create(store=store, session_key="stk")
    with pytest.raises(CartError, match="موجودی"):
        service.add_item(cart, "test-product", quantity=100)


@pytest.mark.django_db
def test_merge_guest_cart(store, product):
    guest_cart = Cart.objects.create(store=store, session_key="guest-merge")
    CartService().add_item(guest_cart, "test-product", quantity=2)

    user = User.objects.create_user(phone="09124445566", phone_verified=True)
    user_cart = Cart.objects.create(store=store, user=user)

    CartService().merge_carts(guest_cart, user_cart)

    user_cart.refresh_from_db()
    assert user_cart.items.count() == 1
    assert user_cart.items.first().quantity == 2
    assert not Cart.objects.filter(pk=guest_cart.pk).exists()


@pytest.mark.django_db
def test_cart_count_api(client, store, product, auth_headers):
    client.post(
        "/api/v1/cart/add",
        data=json.dumps({"product_slug": "test-product", "quantity": 1}),
        content_type="application/json",
        **auth_headers,
    )
    response = client.get("/api/v1/cart/count", **auth_headers)
    assert response.status_code == 200
    assert response.json()["item_count"] == 1


@pytest.mark.django_db
def test_storefront_cart_page(client, store):
    response = client.get("/cart/", HTTP_HOST="cart.local")
    assert response.status_code == 200
    assert "cart-page" in response.content.decode()


@pytest.mark.django_db
def test_storefront_checkout_requires_login(client, store):
    response = client.get("/checkout/", HTTP_HOST="cart.local")
    assert response.status_code == 302
    assert response["Location"].startswith("/login/?next=")
    assert "/checkout/" in response["Location"]


@pytest.mark.django_db
def test_storefront_checkout_allows_authenticated(client, store, user):
    client.force_login(user)
    response = client.get("/checkout/", HTTP_HOST="cart.local")
    assert response.status_code == 200
    assert "checkout-page" in response.content.decode()


@pytest.mark.django_db
def test_variable_product_requires_variant_and_label(store):
    from products.models import ProductAttribute, ProductAttributeValue, ProductVariant

    p = Product.objects.create(
        store=store,
        name="Variable Tee",
        slug="variable-tee",
        status=ProductStatus.ACTIVE,
        base_price=500000,
        product_type=ProductType.VARIABLE,
    )
    attr = ProductAttribute.objects.create(store=store, name="سایز", slug="size", display_type="button")
    val_m = ProductAttributeValue.objects.create(attribute=attr, value="M", slug="m")
    v = ProductVariant.objects.create(product=p, sku="TEE-M", price=520000, is_active=True)
    v.attributes.add(val_m)
    Inventory.objects.create(variant=v, quantity=5)

    service = CartService()
    cart = Cart.objects.create(store=store, session_key="var-session")
    with pytest.raises(CartError, match="تنوع"):
        service.add_item(cart, "variable-tee", quantity=1)

    item = service.add_item(cart, "variable-tee", variant_id=v.id, quantity=1)
    data = service.serialize_cart(cart)
    assert data["items"][0]["variant_id"] == v.id
    assert "سایز" in (data["items"][0]["variant_label"] or "")
    assert "M" in (data["items"][0]["variant_label"] or "")
    assert item.unit_price == v.price
