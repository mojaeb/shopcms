"""Reports tests."""

from decimal import Decimal

import pytest

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from orders.enums import OrderStatus
from orders.models import Order, OrderItem, Shipment
from payments.enums import GatewayType, PaymentStatus
from payments.models import PaymentTransaction
from products.enums import ProductStatus
from products.models import Inventory, Product
from reports.services.report import ReportService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Report Shop", slug="report-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="report.local")
    return s


@pytest.fixture
def customer_role(db):
    return Role.objects.create(codename="customer", name="Customer", scope=RoleScope.STORE)


@pytest.fixture
def reports_role(db):
    role = Role.objects.create(codename="reports", name="Reports", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="reports.view", name="Reports", group="reports")
    role.permissions.add(perm)
    return role


@pytest.fixture
def user(db, store, customer_role):
    u = User.objects.create_user(phone="09121110000", phone_verified=True, first_name="Ali")
    StoreMembership.objects.create(user=u, store=store, role=customer_role, status=MembershipStatus.ACTIVE)
    return u


@pytest.fixture
def staff_user(db, store, reports_role):
    u = User.objects.create_user(phone="09122220000", phone_verified=True, is_staff=True)
    StoreMembership.objects.create(user=u, store=store, role=reports_role, status=MembershipStatus.ACTIVE)
    return u


@pytest.fixture
def product(store):
    p = Product.objects.create(
        store=store, name="T-Shirt", slug="t-shirt", status=ProductStatus.ACTIVE, base_price=100000,
    )
    Inventory.objects.create(product=p, quantity=10, reserved=2, track_inventory=True, low_stock_threshold=5)
    return p


@pytest.fixture
def paid_order(store, user, product):
    order = Order.objects.create(
        store=store,
        user=user,
        order_number="ORD-R001",
        status=OrderStatus.PAID,
        subtotal=100000,
        discount=0,
        shipping_cost=20000,
        tax=9000,
        total=129000,
        shipping_method="Post",
    )
    OrderItem.objects.create(
        order=order,
        product_id=product.id,
        product_name=product.name,
        product_slug=product.slug,
        quantity=2,
        unit_price=50000,
        line_total=100000,
    )
    Shipment.objects.create(order=order, status="pending", carrier="Post")
    PaymentTransaction.objects.create(
        store=store,
        user=user,
        gateway=GatewayType.ZARINPAL,
        amount=129000,
        status=PaymentStatus.PAID,
    )
    return order


@pytest.fixture
def auth_headers(staff_user, store):
    token = JWTService().create_tokens(staff_user.id, store.id, "reports", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "report.local"}


@pytest.mark.django_db
def test_sales_report(store, paid_order):
    report = ReportService().get_sales_report(store, days=30)
    assert report["total_orders"] == 1
    assert report["total_revenue"] == 129000
    assert len(report["top_products"]) == 1


@pytest.mark.django_db
def test_customers_report(store, user, paid_order):
    report = ReportService().get_customers_report(store, days=30)
    assert report["total_customers"] == 1
    assert len(report["top_customers"]) == 1
    assert report["top_customers"][0]["spent"] == 129000


@pytest.mark.django_db
def test_inventory_report(store, product):
    report = ReportService().get_inventory_report(store)
    assert report["tracked_items"] == 1
    assert report["total_available_units"] == 8


@pytest.mark.django_db
def test_payments_report(store, paid_order):
    report = ReportService().get_payments_report(store, days=30)
    assert report["successful_count"] == 1
    assert report["total_paid_amount"] == 129000


@pytest.mark.django_db
def test_shipping_report(store, paid_order):
    report = ReportService().get_shipping_report(store, days=30)
    assert report["total_shipments"] == 1
    assert report["shipping_revenue"] == 20000


@pytest.mark.django_db
def test_summary_report(store, paid_order):
    summary = ReportService().get_summary(store, days=30)
    assert summary["total_revenue"] == 129000
    assert summary["total_customers"] == 1


@pytest.mark.django_db
def test_sales_api(client, auth_headers, paid_order):
    response = client.get("/api/v1/store-admin/reports/sales?days=30", **auth_headers)
    assert response.status_code == 200
    assert response.json()["paid_orders"] == 1


@pytest.mark.django_db
def test_inventory_api(client, auth_headers, product):
    response = client.get("/api/v1/store-admin/reports/inventory", **auth_headers)
    assert response.status_code == 200
    assert response.json()["tracked_items"] == 1
