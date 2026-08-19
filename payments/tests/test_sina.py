"""Sina gateway sandbox tests."""

from decimal import Decimal

import pytest

from payments.models import PaymentTransaction
from payments.providers.sina import SinaGateway
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="S", slug="s-theme", directory="default", is_default=True)
    s = Store.objects.create(name="S Shop", slug="s-shop", default_theme=theme, status="active", currency="IRR")
    Domain.objects.create(store=s, domain="s.local")
    return s


@pytest.fixture
def txn(store, db):
    from accounts.models import User

    user = User.objects.create_user(phone="09120003344", phone_verified=True)
    return PaymentTransaction.objects.create(
        store=store,
        user=user,
        gateway="sina",
        amount=Decimal("150000"),
        tracking_code="TRK-SINA-1",
        authority="",
    )


@pytest.mark.django_db
def test_sina_registered():
    from payments.providers.registry import get_gateway

    gw = get_gateway("sina")
    assert gw is not None
    assert gw.codename == "sina"
    assert gw.label == "سینا"
    assert gw.is_live_ready({}) is False


@pytest.mark.django_db
def test_sina_sandbox_create_and_verify(txn):
    gw = SinaGateway()
    config = {"terminal_id": "sandbox-sina", "sandbox": True}
    created = gw.create_payment(txn, config, "http://s.local/api/v1/payments/callback/sina/")
    assert created.authority
    assert "Authority=" in created.payment_url
    assert "Status=OK" in created.payment_url

    verified = gw.verify_payment(txn, config, {"Authority": created.authority, "Status": "OK"})
    assert verified.success is True
    assert verified.ref_id


@pytest.mark.django_db
def test_sina_live_not_implemented(txn):
    gw = SinaGateway()
    config = {"terminal_id": "live-terminal", "sandbox": False}
    with pytest.raises(ValueError, match="سینا"):
        gw.create_payment(txn, config, "http://s.local/api/v1/payments/callback/sina/")
