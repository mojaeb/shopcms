"""Advanced discount tests."""

import json
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from accounts.enums import RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.jwt import JWTService
from carts.enums import DiscountScope, DiscountType
from carts.models import Cart, Coupon, GiftCard
from carts.services.cart import CartError, CartService
from orders.enums import OrderStatus
from orders.models import Order
from products.enums import ProductStatus, ProductType
from products.models import Category, Inventory, Product
from tenants.models import Domain, Plugin, Store, StorePlugin, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Disc Shop", slug="disc-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="disc.local")
    plugin, _ = Plugin.objects.get_or_create(codename="coupon", defaults={"name": "Coupons", "is_active": True})
    StorePlugin.objects.create(store=s, plugin=plugin, is_enabled=True)
    return s


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="09128889900", phone_verified=True)


@pytest.fixture
def product(store):
    p = Product.objects.create(
        store=store, name="Disc Product", slug="disc-product",
        status=ProductStatus.ACTIVE, base_price=1000000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=p, quantity=10)
    return p


@pytest.fixture
def cart(store, user, product):
    service = CartService()
    c = Cart.objects.create(store=store, user=user, session_key="disc-cart")
    service.add_item(c, "disc-product", quantity=1)
    return c


@pytest.fixture
def admin_role(db):
    return Role.objects.create(codename="store_admin", name="Admin", scope=RoleScope.STORE)


@pytest.fixture
def admin_user(db, store, admin_role):
    u = User.objects.create_user(phone="09127776655", phone_verified=True)
    StoreMembership.objects.create(user=u, store=store, role=admin_role)
    return u


@pytest.fixture
def admin_headers(admin_user, store):
    token = JWTService().create_tokens(admin_user.id, store.id, "store_admin", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "disc.local"}


@pytest.mark.django_db
def test_first_purchase_coupon(store, cart, user):
    Coupon.objects.create(
        store=store, code="FIRST", discount_type=DiscountType.PERCENTAGE, value=20,
        first_purchase_only=True, is_active=True,
    )
    service = CartService()
    service.apply_coupon(cart, "FIRST")
    assert service.calculate_totals(cart)["discount"] == Decimal("200000")

    Order.objects.create(
        store=store, user=user, order_number="ORD-TEST", status=OrderStatus.PAID, total=100,
    )
    cart.coupon = None
    cart.save()
    service.add_item(cart, "disc-product", quantity=1)
    with pytest.raises(CartError, match="اولین خرید"):
        service.apply_coupon(cart, "FIRST")


@pytest.mark.django_db
def test_category_scoped_coupon(store, cart, product):
    other = Product.objects.create(
        store=store, name="Other", slug="other", status=ProductStatus.ACTIVE,
        base_price=500000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=other, quantity=5)
    category = Category.objects.create(store=store, name="Special", slug="special")
    product.category = category
    product.save()

    service = CartService()
    service.add_item(cart, "other", quantity=1)

    coupon = Coupon.objects.create(
        store=store, code="CAT20", discount_type=DiscountType.PERCENTAGE, value=20,
        scope=DiscountScope.CATEGORY, is_active=True,
    )
    coupon.categories.add(category)

    cart.coupon = coupon
    cart.save()
    totals = service.calculate_totals(cart)
    assert totals["coupon_discount"] == Decimal("200000")


@pytest.mark.django_db
def test_user_restricted_coupon(store, cart, user):
    other = User.objects.create_user(phone="09120001122", phone_verified=True)
    coupon = Coupon.objects.create(
        store=store, code="VIP", discount_type=DiscountType.FIXED, value=100000, is_active=True,
    )
    coupon.allowed_users.add(other)

    service = CartService()
    with pytest.raises(CartError, match="مجاز"):
        service.apply_coupon(cart, "VIP")


@pytest.mark.django_db
def test_expired_coupon(store, cart):
    Coupon.objects.create(
        store=store, code="OLD", discount_type=DiscountType.FIXED, value=10000,
        is_active=True, valid_until=timezone.now() - timedelta(days=1),
    )
    with pytest.raises(CartError, match="منقضی"):
        CartService().apply_coupon(cart, "OLD")


@pytest.mark.django_db
def test_gift_card_apply(store, cart):
    GiftCard.objects.create(store=store, code="GIFT50", initial_balance=500000, balance=500000, is_active=True)
    service = CartService()
    service.apply_gift_card(cart, "GIFT50")
    totals = service.calculate_totals(cart)
    assert totals["gift_discount"] == Decimal("500000")
    assert totals["total"] == Decimal("500000")


@pytest.mark.django_db
def test_gift_card_mutually_exclusive_with_coupon(store, cart):
    Coupon.objects.create(
        store=store, code="CPN", discount_type=DiscountType.PERCENTAGE, value=10, is_active=True,
    )
    GiftCard.objects.create(store=store, code="GIFT", initial_balance=100000, balance=100000, is_active=True)
    service = CartService()
    service.apply_coupon(cart, "CPN")
    service.apply_gift_card(cart, "GIFT")
    cart.refresh_from_db()
    assert cart.gift_card_id
    assert cart.coupon_id is None


@pytest.mark.django_db
def test_coupon_admin_api(client, store, admin_headers):
    response = client.post(
        "/api/v1/store-admin/discounts/coupons",
        data=json.dumps({
            "code": "ADMIN10",
            "discount_type": "percentage",
            "value": 10,
            "scope": "all",
        }),
        content_type="application/json",
        **admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["code"] == "ADMIN10"


@pytest.mark.django_db
def test_gift_card_admin_api(client, store, admin_headers):
    response = client.post(
        "/api/v1/store-admin/discounts/gift-cards",
        data=json.dumps({"code": "GC100", "initial_balance": 100000}),
        content_type="application/json",
        **admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["balance"] == "100000"
