"""Tests for shipment SMS notifications."""

from unittest.mock import MagicMock, patch

import pytest

from accounts.enums import RoleScope
from accounts.models import Role, StoreMembership, User
from addresses.models import CustomerAddress
from carts.models import Cart, CartItem
from orders.enums import OrderStatus
from orders.models import Order, Shipment
from orders.services.order import OrderService
from payments.enums import PaymentStatus
from payments.models import PaymentTransaction
from payments.services.payment import PaymentService
from products.enums import ProductStatus, ProductType
from products.models import Inventory, Product
from shipping.enums import CalculationMode, ShippingProviderType
from shipping.models import ShippingMethod, ShippingZone
from tenants.models import Domain, Store, StoreSetting, Theme


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default-sms", directory="default", is_default=False)
    s = Store.objects.create(name="SMS Shop", slug="sms-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="sms.local")
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
def user(db, store, customer_role):
    u = User.objects.create_user(phone="09125551234", phone_verified=True)
    StoreMembership.objects.create(user=u, store=store, role=customer_role)
    return u


@pytest.fixture
def address(user, store):
    return CustomerAddress.objects.create(
        user=user, store=store,
        full_name="Test User", phone="09125551234",
        province="Tehran", city="Tehran",
        postal_code="1234567890", address_line="Street 1",
        is_default=True,
    )


@pytest.fixture
def shipping_method(store):
    zone = ShippingZone.objects.create(store=store, name="All")
    return ShippingMethod.objects.create(
        store=store, zone=zone, name="Post", slug="post-sms",
        provider=ShippingProviderType.POST, calculation_mode=CalculationMode.FIXED,
        config={"fixed_price": 50000},
    )


@pytest.fixture
def cart_with_items(store, user):
    product = Product.objects.create(
        store=store, name="SMS Item", slug="sms-item", status=ProductStatus.ACTIVE,
        base_price=300000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=product, quantity=10)
    cart = Cart.objects.create(store=store, user=user, session_key="sms-cart")
    CartItem.objects.create(cart=cart, product=product, quantity=1, unit_price=300000)
    return cart


class FakeRequest:
    def __init__(self, user_obj):
        self.user = user_obj
        self.META = {}
        self.session = type("S", (), {"session_key": "sms-session", "create": lambda self: None})()

    def get_host(self):
        return "sms.local"

    def is_secure(self):
        return False


@pytest.fixture
def paid_order(store, user, cart_with_items, address, shipping_method):
    service = PaymentService()
    request = FakeRequest(user)
    txn = service.create_payment(store, user, "zarinpal", address.id, shipping_method.id, 50000, request)
    service.verify_payment(txn, {"Authority": txn.authority, "Status": "OK"})
    return Order.objects.select_related("user", "store").get(payment=txn)


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_sms_sent_on_shipped_when_enabled(store, paid_order):
    StoreSetting.objects.create(store=store, group="notifications", key="shipment_sms_enabled", value=True)

    with patch("orders.services.order._notification_service.send_sms") as mock_sms:
        OrderService().update_status(paid_order, OrderStatus.SENT)

    mock_sms.assert_called_once()
    call_kwargs = mock_sms.call_args
    body = call_kwargs[0][1] if call_kwargs[0] else call_kwargs[1].get("message", "")
    assert "ارسال شد" in body


@pytest.mark.django_db
def test_sms_sent_on_delivered_when_enabled(store, paid_order):
    StoreSetting.objects.create(store=store, group="notifications", key="shipment_sms_enabled", value=True)

    with patch("orders.services.order._notification_service.send_sms") as mock_sms:
        OrderService().update_status(paid_order, OrderStatus.SENT)
        mock_sms.reset_mock()
        paid_order.refresh_from_db()
        OrderService().update_status(paid_order, OrderStatus.DELIVERED)

    mock_sms.assert_called_once()
    body = mock_sms.call_args[0][1]
    assert "تحویل داده شد" in body


@pytest.mark.django_db
def test_sms_not_sent_when_disabled(store, paid_order):
    # shipment_sms_enabled پیش‌فرض False است؛ هیچ StoreSetting ای ست نمی‌کنیم.
    with patch("orders.services.order._notification_service.send_sms") as mock_sms:
        OrderService().update_status(paid_order, OrderStatus.SENT)

    mock_sms.assert_not_called()


@pytest.mark.django_db
def test_sms_failure_does_not_fail_update_status(store, paid_order):
    """اگر send_sms خطا بدهد، update_status باید بدون مشکل کامل شود."""
    from notifications.services.notification import NotificationError

    StoreSetting.objects.create(store=store, group="notifications", key="shipment_sms_enabled", value=True)

    with patch("orders.services.order._notification_service.send_sms", side_effect=NotificationError("خطا")):
        order = OrderService().update_status(paid_order, OrderStatus.SENT)

    order.refresh_from_db()
    assert order.status == OrderStatus.SENT  # سفارش موفق ثبت شده


@pytest.mark.django_db
def test_sms_not_sent_twice_on_same_status(store, paid_order):
    """اگر update_shipment با همان status دوباره صدا زده شود، پیامک تکراری نرود."""
    StoreSetting.objects.create(store=store, group="notifications", key="shipment_sms_enabled", value=True)
    svc = OrderService()

    with patch("orders.services.order._notification_service.send_sms") as mock_sms:
        svc.update_shipment(paid_order, status="shipped")
        first_count = mock_sms.call_count
        svc.update_shipment(paid_order, tracking_code="TRK123")  # status تغییر نکرده
        second_count = mock_sms.call_count

    assert first_count == 1
    assert second_count == 1  # پیامک دوم نرفته


@pytest.mark.django_db
def test_update_shipment_sms_on_status_change(store, paid_order):
    StoreSetting.objects.create(store=store, group="notifications", key="shipment_sms_enabled", value=True)

    with patch("orders.services.order._notification_service.send_sms") as mock_sms:
        OrderService().update_shipment(paid_order, tracking_code="TRK999", status="shipped")

    mock_sms.assert_called_once()
    body = mock_sms.call_args[0][1]
    assert "TRK999" in body
