"""Zarinpal gateway unit tests."""

from decimal import Decimal
from unittest.mock import patch

import pytest

from payments.models import PaymentTransaction
from payments.providers.zarinpal import ZarinpalGateway
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Z", slug="z-theme", directory="default", is_default=True)
    s = Store.objects.create(name="Z Shop", slug="z-shop", default_theme=theme, status="active", currency="IRR")
    Domain.objects.create(store=s, domain="z.local")
    return s


@pytest.fixture
def txn(store, db):
    from accounts.models import User

    user = User.objects.create_user(phone="09120001122", phone_verified=True)
    return PaymentTransaction.objects.create(
        store=store,
        user=user,
        gateway="zarinpal",
        amount=Decimal("150000"),
        tracking_code="TRK-TEST-1",
        authority="",
    )


@pytest.mark.django_db
def test_zarinpal_registered():
    from payments.providers.registry import get_gateway

    gw = get_gateway("zarinpal")
    assert gw is not None
    assert gw.codename == "zarinpal"
    assert gw.label == "زرین‌پال"


@pytest.mark.django_db
def test_zarinpal_simulate_create_and_verify(txn):
    gw = ZarinpalGateway()
    config = {"merchant_id": "sandbox-merchant", "sandbox": True}
    created = gw.create_payment(txn, config, "http://z.local/api/v1/payments/callback/zarinpal/")
    assert created.authority.startswith("S")
    assert "Authority=" in created.payment_url
    assert "Status=OK" in created.payment_url

    verified = gw.verify_payment(txn, config, {"Authority": created.authority, "Status": "OK"})
    assert verified.success is True
    assert verified.ref_id


@pytest.mark.django_db
def test_zarinpal_live_request_uses_api(txn):
    gw = ZarinpalGateway()
    config = {
        "merchant_id": "1344b5d4-0048-11e8-94db-005056a205be",
        "sandbox": False,
        "simulate": False,
    }
    fake_response = {
        "data": {"code": 100, "authority": "A00000000000000000000000000000000001", "message": "Success"},
        "errors": [],
    }
    with patch.object(gw, "_post", return_value=fake_response) as post:
        created = gw.create_payment(txn, config, "https://shop.example/callback/")
        assert created.authority == "A00000000000000000000000000000000001"
        assert created.payment_url.endswith("/pg/StartPay/A00000000000000000000000000000000001")
        post.assert_called_once()
        args, _kwargs = post.call_args
        assert args[0].endswith("/request.json")
        assert args[1]["amount"] == 150000
        assert args[1]["currency"] == "IRR"


@pytest.mark.django_db
def test_zarinpal_live_verify(txn):
    gw = ZarinpalGateway()
    config = {
        "merchant_id": "1344b5d4-0048-11e8-94db-005056a205be",
        "sandbox": False,
        "simulate": False,
    }
    txn.authority = "A00000000000000000000000000000000001"
    fake_response = {
        "data": {"code": 100, "ref_id": 987654, "message": "Verified"},
        "errors": [],
    }
    with patch.object(gw, "_post", return_value=fake_response):
        result = gw.verify_payment(txn, config, {"Authority": txn.authority, "Status": "OK"})
    assert result.success is True
    assert result.ref_id == "987654"


@pytest.mark.django_db
def test_zarinpal_requires_merchant_id(txn):
    gw = ZarinpalGateway()
    with pytest.raises(ValueError, match="merchant_id"):
        gw.create_payment(txn, {"sandbox": True, "simulate": True}, "http://cb/")
