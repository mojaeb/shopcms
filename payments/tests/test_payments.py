"""Payment tests."""

import json

import pytest

from accounts.models import User
from accounts.services.jwt import JWTService
from carts.models import Cart, CartItem
from payments.enums import PaymentStatus
from payments.models import PaymentTransaction
from payments.services.payment import PaymentError, PaymentService
from products.enums import ProductStatus, ProductType
from products.models import Inventory, Product
from tenants.models import Domain, Store, StoreSetting, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Pay Shop", slug="pay-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="pay.local")
    StoreSetting.objects.create(
        store=s, group="payment", key="gateways", value=["zarinpal", "idpay"],
    )
    StoreSetting.objects.create(
        store=s, group="payment", key="default_gateway", value="zarinpal",
    )
    StoreSetting.objects.create(
        store=s, group="payment", key="zarinpal", value={"merchant_id": "test", "sandbox": True},
    )
    StoreSetting.objects.create(
        store=s, group="payment", key="idpay", value={"api_key": "test", "sandbox": True},
    )
    return s


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="09126667788", phone_verified=True)


@pytest.fixture
def auth_headers(user, store):
    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "pay.local"}


@pytest.fixture
def cart_with_items(store, user):
    product = Product.objects.create(
        store=store, name="Pay Item", slug="pay-item", status=ProductStatus.ACTIVE,
        base_price=500000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=product, quantity=10)
    cart = Cart.objects.create(store=store, user=user, session_key="pay-cart")
    CartItem.objects.create(cart=cart, product=product, quantity=1, unit_price=500000)
    return cart


@pytest.mark.django_db
def test_list_gateways_api(client, store):
    response = client.get("/api/v1/payments/gateways", HTTP_HOST="pay.local")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.django_db
def test_create_payment_api(client, store, user, auth_headers, cart_with_items):
    response = client.post(
        "/api/v1/payments/create",
        data=json.dumps({
            "gateway": "zarinpal",
            "address_id": 1,
            "shipping_method_id": 1,
            "shipping_price": 50000,
        }),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gateway"] == "zarinpal"
    assert data["amount"] == "550000"
    assert data["payment_url"]


@pytest.mark.django_db
def test_verify_payment_flow(store, user, cart_with_items):
    service = PaymentService()

    class FakeRequest:
        def __init__(self, user_obj):
            self.user = user_obj
            self.META = {}
            self.session = type("S", (), {"session_key": "x", "create": lambda self: None})()

        def get_host(self):
            return "pay.local"

        def is_secure(self):
            return False

    request = FakeRequest(user)
    txn = service.create_payment(store, user, "zarinpal", 1, 1, 50000, request)
    assert txn.status == PaymentStatus.REDIRECTED

    verified = service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})
    assert verified.status == PaymentStatus.PAID
    assert verified.ref_id


@pytest.mark.django_db
def test_payment_callback_redirect(client, store, user, cart_with_items):
    service = PaymentService()

    class FakeRequest:
        def __init__(self, user_obj):
            self.user = user_obj
            self.META = {}
            self.session = type("S", (), {"session_key": "cb", "create": lambda self: None})()

        def get_host(self):
            return "pay.local"

        def is_secure(self):
            return False

    txn = service.create_payment(store, user, "zarinpal", 1, 1, 50000, FakeRequest(user))
    response = client.get(
        f"/api/v1/payments/callback/zarinpal/?Authority={txn.authority}&Status=OK",
        HTTP_HOST="pay.local",
    )
    assert response.status_code == 302
    assert "tracking=" in response.url


@pytest.mark.django_db
def test_refund_payment(store, user):
    txn = PaymentTransaction.objects.create(
        store=store, user=user, gateway="zarinpal", amount=100000, status=PaymentStatus.PAID,
    )
    service = PaymentService()
    refunded = service.refund_payment(txn)
    assert refunded.status == PaymentStatus.REFUNDED
    assert refunded.refunded_amount == 100000


@pytest.mark.django_db
def test_webhook_verify(store, user):
    service = PaymentService()
    txn = PaymentTransaction.objects.create(
        store=store, user=user, gateway="zarinpal", amount=100000,
        authority="webhook-auth", status=PaymentStatus.REDIRECTED,
    )
    result = service.handle_webhook(store, "zarinpal", {"Authority": "webhook-auth", "Status": "OK"})
    assert result.status == PaymentStatus.PAID


@pytest.mark.django_db
def test_create_requires_auth(client, store, cart_with_items):
    response = client.post(
        "/api/v1/payments/create",
        data=json.dumps({
            "gateway": "zarinpal",
            "address_id": 1,
            "shipping_method_id": 1,
            "shipping_price": 50000,
        }),
        content_type="application/json",
        HTTP_HOST="pay.local",
    )
    assert response.status_code == 401
