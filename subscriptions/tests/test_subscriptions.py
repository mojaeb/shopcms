"""Subscription tests."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from accounts.enums import RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.jwt import JWTService
from orders.models import Order, OrderItem
from plugins.services.plugin import PluginService
from products.enums import ProductStatus, ProductType
from products.models import Product
from subscriptions.enums import BillingInterval, SubscriptionStatus
from subscriptions.models import CustomerSubscription
from subscriptions.services.subscription import SubscriptionError, SubscriptionService
from tenants.enums import StoreType
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(
        name="Sub Shop",
        slug="sub-shop",
        default_theme=theme,
        status="active",
        store_type=StoreType.SUBSCRIPTION,
    )
    Domain.objects.create(store=s, domain="sub.local")
    PluginService().sync_registry_to_db()
    PluginService().install_defaults(s)
    return s


@pytest.fixture
def user(db, store):
    role = Role.objects.create(codename="customer", name="Customer", scope=RoleScope.STORE)
    u = User.objects.create_user(phone="09123334455", phone_verified=True)
    StoreMembership.objects.create(user=u, store=store, role=role)
    return u


@pytest.fixture
def product(store):
    return Product.objects.create(
        store=store,
        name="Premium",
        slug="premium",
        product_type=ProductType.SUBSCRIPTION,
        status=ProductStatus.ACTIVE,
        base_price=99000,
    )


@pytest.fixture
def plan(store, product):
    return SubscriptionService().create_plan(
        store, product.id, BillingInterval.MONTHLY, Decimal("99000"), trial_days=7,
    )


@pytest.fixture
def order(store, user, product):
    order = Order.objects.create(
        store=store,
        user=user,
        order_number="ORD-SUB01",
        status="paid",
        subtotal=99000,
        total=99000,
    )
    OrderItem.objects.create(
        order=order,
        product_id=product.id,
        product_name=product.name,
        product_slug=product.slug,
        quantity=1,
        unit_price=99000,
        line_total=99000,
    )
    return order


@pytest.fixture
def auth_headers(user, store):
    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "sub.local"}


@pytest.mark.django_db
def test_create_plan(store, product):
    plan = SubscriptionService().create_plan(store, product.id, BillingInterval.MONTHLY, Decimal("50000"))
    product.refresh_from_db()
    assert product.product_type == ProductType.SUBSCRIPTION
    assert plan.interval == BillingInterval.MONTHLY


@pytest.mark.django_db
def test_create_subscription_from_order(store, user, plan, order):
    subs = SubscriptionService().create_from_order(order)
    assert len(subs) == 1
    sub = subs[0]
    assert sub.status == SubscriptionStatus.TRIALING
    assert sub.trial_ends_at is not None


@pytest.mark.django_db
def test_renew_subscription(store, user, plan, order):
    service = SubscriptionService()
    sub = service.create_from_order(order)[0]
    sub.status = SubscriptionStatus.ACTIVE
    sub.trial_ends_at = None
    sub.save()
    old_end = sub.current_period_end
    service.renew(sub, payment_ref="test")
    sub.refresh_from_db()
    assert sub.current_period_end > old_end
    assert sub.renewal_count == 1


@pytest.mark.django_db
def test_cancel_subscription(store, user, plan, order):
    sub = SubscriptionService().create_from_order(order)[0]
    canceled = SubscriptionService().cancel(sub, immediate=False)
    assert canceled.status == SubscriptionStatus.CANCELED
    assert canceled.auto_renew is False


@pytest.mark.django_db
def test_expire_subscriptions(store, user, plan, order):
    service = SubscriptionService()
    sub = service.create_from_order(order)[0]
    sub.status = SubscriptionStatus.ACTIVE
    sub.trial_ends_at = None
    sub.current_period_end = timezone.now() - timedelta(days=10)
    sub.save()
    count = service.expire_due_subscriptions(store=store)
    sub.refresh_from_db()
    assert sub.status == SubscriptionStatus.EXPIRED
    assert count >= 1


@pytest.mark.django_db
def test_list_subscriptions_api(client, auth_headers, plan, order):
    SubscriptionService().create_from_order(order)
    response = client.get("/api/v1/subscriptions/", **auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_renew_api(client, auth_headers, plan, order):
    service = SubscriptionService()
    sub = service.create_from_order(order)[0]
    sub.status = SubscriptionStatus.ACTIVE
    sub.trial_ends_at = None
    sub.auto_renew = False
    sub.save()
    response = client.post(f"/api/v1/subscriptions/{sub.id}/renew", **auth_headers)
    assert response.status_code == 200
    assert response.json()["renewal_count"] == 1
