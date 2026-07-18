"""End-to-end API integration: cart → payment → order."""

import json

import pytest
from django.test import Client

from accounts.enums import RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.jwt import JWTService
from addresses.models import CustomerAddress
from orders.enums import OrderStatus
from orders.models import Order
from payments.enums import PaymentStatus
from payments.services.payment import PaymentService
from products.enums import ProductStatus, ProductType
from products.models import Inventory, Product
from shipping.enums import CalculationMode, ShippingProviderType
from shipping.models import ShippingMethod, ShippingZone
from tenants.models import Domain, Store, StoreSetting, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="E2E Shop", slug="e2e-shop", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="e2e.local")
    StoreSetting.objects.create(store=store, group="payment", key="gateways", value=["zarinpal"])
    StoreSetting.objects.create(store=store, group="payment", key="default_gateway", value="zarinpal")
    StoreSetting.objects.create(
        store=store,
        group="payment",
        key="zarinpal",
        value={"merchant_id": "test", "sandbox": True},
    )
    return store


@pytest.fixture
def customer(store):
    role = Role.objects.create(codename="customer", name="Customer", scope=RoleScope.STORE, is_system=True)
    user = User.objects.create_user(phone="09128887766", phone_verified=True)
    StoreMembership.objects.create(user=user, store=store, role=role)
    return user


@pytest.fixture
def product(store):
    product = Product.objects.create(
        store=store,
        name="E2E Product",
        slug="e2e-product",
        status=ProductStatus.ACTIVE,
        base_price=500000,
        product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=product, quantity=20)
    return product


@pytest.fixture
def auth_headers(customer, store):
    token = JWTService().create_tokens(customer.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "e2e.local"}


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_full_checkout_api_flow(client, store, customer, product, auth_headers):
    add = client.post(
        "/api/v1/cart/add",
        data=json.dumps({"product_slug": "e2e-product", "quantity": 2}),
        content_type="application/json",
        **auth_headers,
    )
    assert add.status_code == 200
    assert add.json()["item_count"] == 2

    address = CustomerAddress.objects.create(
        user=customer,
        store=store,
        full_name="E2E User",
        phone=customer.phone,
        province="Tehran",
        city="Tehran",
        postal_code="1234567890",
        address_line="Integration Street",
        is_default=True,
    )
    zone = ShippingZone.objects.create(store=store, name="Tehran")
    shipping = ShippingMethod.objects.create(
        store=store,
        zone=zone,
        name="Post",
        slug="post",
        provider=ShippingProviderType.POST,
        calculation_mode=CalculationMode.FIXED,
        config={"fixed_price": 40000},
    )

    class FakeRequest:
        def __init__(self, user_obj):
            self.user = user_obj
            self.META = {}
            self.session = type("S", (), {"session_key": "e2e-session", "create": lambda self: None})()

        def get_host(self):
            return "e2e.local"

        def is_secure(self):
            return False

    payment_service = PaymentService()
    txn = payment_service.create_payment(
        store,
        customer,
        "zarinpal",
        address.id,
        shipping.id,
        40000,
        FakeRequest(customer),
    )
    verified = payment_service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})
    assert verified.status == PaymentStatus.PAID

    order = Order.objects.get(payment=verified)
    assert order.status == OrderStatus.PAID
    assert order.total == 1040000

    orders_api = client.get("/api/v1/orders/", **auth_headers)
    assert orders_api.status_code == 200
    assert len(orders_api.json()) == 1
    assert orders_api.json()[0]["status"] == OrderStatus.PAID

    detail = client.get(f"/api/v1/orders/{order.id}", **auth_headers)
    assert detail.status_code == 200
    assert detail.json()["items"][0]["quantity"] == 2

    health = client.get("/api/v1/health/")
    assert health.status_code == 200
    assert health.json()["database"] == "ok"
