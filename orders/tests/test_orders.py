"""Order tests."""

import json

import pytest

from accounts.enums import RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from addresses.models import CustomerAddress
from carts.models import Cart, CartItem
from orders.enums import OrderStatus
from orders.models import Order, OrderItem
from orders.services.order import OrderError, OrderService
from payments.enums import PaymentStatus
from payments.models import PaymentTransaction
from payments.services.payment import PaymentService
from products.enums import ProductStatus, ProductType
from products.models import Inventory, Product
from shipping.enums import CalculationMode, ShippingProviderType
from shipping.models import ShippingMethod, ShippingZone
from tenants.models import Domain, Store, StoreSetting, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Order Shop", slug="order-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="order.local")
    StoreSetting.objects.create(store=s, group="payment", key="gateways", value=["zarinpal"])
    StoreSetting.objects.create(store=s, group="payment", key="default_gateway", value="zarinpal")
    StoreSetting.objects.create(
        store=s, group="payment", key="zarinpal", value={"merchant_id": "test", "sandbox": True},
    )
    return s


@pytest.fixture
def customer_role(db):
    return Role.objects.create(codename="customer", name="Customer", scope=RoleScope.STORE)


@pytest.fixture
def orders_role(db):
    role = Role.objects.create(codename="orders", name="Orders", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="orders.view", name="View Orders", group="orders")
    role.permissions.add(perm)
    return role


@pytest.fixture
def user(db, store, customer_role):
    u = User.objects.create_user(phone="09129998877", phone_verified=True)
    StoreMembership.objects.create(user=u, store=store, role=customer_role)
    return u


@pytest.fixture
def staff_user(db, store, orders_role):
    u = User.objects.create_user(phone="09121112233", phone_verified=True)
    StoreMembership.objects.create(user=u, store=store, role=orders_role)
    return u


@pytest.fixture
def auth_headers(user, store):
    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "order.local"}


@pytest.fixture
def staff_headers(staff_user, store):
    token = JWTService().create_tokens(staff_user.id, store.id, "orders", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "order.local"}


@pytest.fixture
def address(user, store):
    return CustomerAddress.objects.create(
        user=user,
        store=store,
        full_name="Test User",
        phone="09129998877",
        province="Tehran",
        city="Tehran",
        postal_code="1234567890",
        address_line="Test Street 1",
        is_default=True,
    )


@pytest.fixture
def shipping_method(store):
    zone = ShippingZone.objects.create(store=store, name="Tehran")
    return ShippingMethod.objects.create(
        store=store,
        zone=zone,
        name="Post",
        slug="post",
        provider=ShippingProviderType.POST,
        calculation_mode=CalculationMode.FIXED,
        config={"fixed_price": 50000},
    )


@pytest.fixture
def cart_with_items(store, user):
    product = Product.objects.create(
        store=store, name="Order Item", slug="order-item", status=ProductStatus.ACTIVE,
        base_price=400000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=product, quantity=10)
    cart = Cart.objects.create(store=store, user=user, session_key="order-cart")
    CartItem.objects.create(cart=cart, product=product, quantity=2, unit_price=400000)
    return cart


class FakeRequest:
    def __init__(self, user_obj):
        self.user = user_obj
        self.META = {}
        self.session = type("S", (), {"session_key": "order-session", "create": lambda self: None})()

    def get_host(self):
        return "order.local"

    def is_secure(self):
        return False


@pytest.mark.django_db
def test_create_order_from_payment(store, user, cart_with_items, address, shipping_method):
    service = PaymentService()
    request = FakeRequest(user)
    txn = service.create_payment(
        store, user, "zarinpal", address.id, shipping_method.id, 50000, request,
    )
    verified = service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})
    assert verified.status == PaymentStatus.PAID

    order = Order.objects.get(payment=verified)
    assert order.status == OrderStatus.PAID
    assert order.items.count() == 1
    assert order.items.first().quantity == 2
    assert order.total == 850000
    assert order.shipment
    assert order.invoice
    assert cart_with_items.items.count() == 0


@pytest.mark.django_db
def test_create_order_idempotent(store, user, cart_with_items, address, shipping_method):
    service = PaymentService()
    request = FakeRequest(user)
    txn = service.create_payment(
        store, user, "zarinpal", address.id, shipping_method.id, 50000, request,
    )
    service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})
    txn.refresh_from_db()
    service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})
    assert Order.objects.filter(payment=txn).count() == 1


@pytest.mark.django_db
def test_list_orders_api(client, store, user, auth_headers, cart_with_items, address, shipping_method):
    service = PaymentService()
    request = FakeRequest(user)
    txn = service.create_payment(
        store, user, "zarinpal", address.id, shipping_method.id, 50000, request,
    )
    service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})

    response = client.get("/api/v1/orders/", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["order_number"].startswith("ORD-")


@pytest.mark.django_db
def test_order_detail_api(client, store, user, auth_headers, cart_with_items, address, shipping_method):
    service = PaymentService()
    request = FakeRequest(user)
    txn = service.create_payment(
        store, user, "zarinpal", address.id, shipping_method.id, 50000, request,
    )
    service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})
    order = Order.objects.get(payment=txn)

    response = client.get(f"/api/v1/orders/{order.id}", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["address"]["full_name"] == "Test User"
    assert data["invoice"]["invoice_number"].startswith("INV-")


@pytest.mark.django_db
def test_store_admin_orders_api(client, store, user, staff_headers, cart_with_items, address, shipping_method):
    service = PaymentService()
    request = FakeRequest(user)
    txn = service.create_payment(
        store, user, "zarinpal", address.id, shipping_method.id, 50000, request,
    )
    service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})

    response = client.get("/api/v1/store-admin/orders/", **staff_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["items"][0]["user"]["phone"] == user.phone


@pytest.mark.django_db
def test_update_order_status(client, store, user, staff_headers, cart_with_items, address, shipping_method):
    service = PaymentService()
    request = FakeRequest(user)
    txn = service.create_payment(
        store, user, "zarinpal", address.id, shipping_method.id, 50000, request,
    )
    service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})
    order = Order.objects.get(payment=txn)

    response = client.put(
        f"/api/v1/store-admin/orders/{order.id}/status",
        data=json.dumps({"status": OrderStatus.PREPARING, "note": "packing"}),
        content_type="application/json",
        **staff_headers,
    )
    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == OrderStatus.PREPARING


@pytest.mark.django_db
def test_invoice_api(client, store, user, auth_headers, cart_with_items, address, shipping_method):
    service = PaymentService()
    request = FakeRequest(user)
    txn = service.create_payment(
        store, user, "zarinpal", address.id, shipping_method.id, 50000, request,
    )
    service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})
    order = Order.objects.get(payment=txn)

    response = client.get(f"/api/v1/orders/{order.id}/invoice", **auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pdf_available"] is False
    assert "PDF" in data["message"]
