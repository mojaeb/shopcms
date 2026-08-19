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
def test_zarinpal_custom_urls(txn):
    gw = ZarinpalGateway()
    config = {
        "merchant_id": "1344b5d4-0048-11e8-94db-005056a205be",
        "sandbox": False,
        "simulate": False,
        "api_base": "https://pay.proxy.example/pg/v4/payment",
        "start_pay_url": "https://pay.proxy.example/StartPay/{authority}",
        "graphql_url": "https://pay.proxy.example/graphql",
    }
    fake_response = {
        "data": {"code": 100, "authority": "A00000000000000000000000000000000001", "message": "Success"},
        "errors": [],
    }
    with patch.object(gw, "_post", return_value=fake_response) as post:
        created = gw.create_payment(txn, config, "https://shop.example/callback/")
    assert created.payment_url == "https://pay.proxy.example/StartPay/A00000000000000000000000000000000001"
    assert post.call_args[0][0] == "https://pay.proxy.example/pg/v4/payment/request.json"
    assert gw._graphql_endpoint(config) == "https://pay.proxy.example/graphql"


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
def test_zarinpal_live_inquiry(txn):
    gw = ZarinpalGateway()
    config = {
        "merchant_id": "1344b5d4-0048-11e8-94db-005056a205be",
        "sandbox": False,
        "simulate": False,
    }
    txn.authority = "A00000000000000000000000000000000001"
    fake_response = {
        "data": {"status": "PAID", "code": 100, "message": "Success"},
        "errors": [],
    }
    with patch.object(gw, "_post", return_value=fake_response) as post:
        result = gw.inquiry_payment(txn, config)
    assert result.success is True
    assert result.status == "PAID"
    post.assert_called_once()
    args, _kwargs = post.call_args
    assert args[0].endswith("/inquiry.json")
    assert args[1]["authority"] == txn.authority
    assert args[1]["merchant_id"] == config["merchant_id"]
    assert "amount" not in args[1]


@pytest.mark.django_db
def test_zarinpal_simulate_inquiry(txn):
    gw = ZarinpalGateway()
    config = {"merchant_id": "sandbox-merchant", "sandbox": True}
    txn.authority = "Sabc"
    result = gw.inquiry_payment(txn, config)
    assert result.success is True
    assert result.status == "PAID"


@pytest.mark.django_db
def test_zarinpal_live_refund_graphql(txn):
    gw = ZarinpalGateway()
    config = {
        "merchant_id": "1344b5d4-0048-11e8-94db-005056a205be",
        "sandbox": False,
        "simulate": False,
        "access_token": "test-access-token",
    }
    txn.authority = "A00000000000000000000000000000000001"
    session_resp = {"data": {"Session": [{"id": "385404123"}]}}
    refund_resp = {
        "data": {
            "resource": {
                "id": "386426364",
                "amount": 150000,
                "timeline": {"refund_status": "PENDING", "refund_amount": 150000},
            }
        }
    }
    with patch.object(gw, "_graphql_post", side_effect=[session_resp, refund_resp]) as gql:
        result = gw.refund_payment(txn, config, Decimal("150000"))
    assert result.success is True
    assert result.refunded_amount == Decimal("150000")
    assert gql.call_count == 2
    session_query, session_vars, token = gql.call_args_list[0][0]
    assert "Session" in session_query
    assert session_vars["authority"] == txn.authority
    assert token == "test-access-token"
    _, refund_vars, _token = gql.call_args_list[1][0]
    assert refund_vars["session_id"] == "385404123"
    assert refund_vars["amount"] == 150000
    assert refund_vars["method"] == "PAYA"
    assert refund_vars["reason"] == "CUSTOMER_REQUEST"


@pytest.mark.django_db
def test_zarinpal_live_refund_requires_access_token(txn):
    gw = ZarinpalGateway()
    config = {
        "merchant_id": "1344b5d4-0048-11e8-94db-005056a205be",
        "sandbox": False,
        "simulate": False,
    }
    result = gw.refund_payment(txn, config, Decimal("150000"))
    assert result.success is False
    assert "پنل پذیرنده" in result.message


def test_zarinpal_error_code_fallback():
    gw = ZarinpalGateway()
    msg = gw._error_message({"errors": {"code": -54}})
    assert "نامعتبر" in msg
    inquiry_msg = gw._error_message({
        "message": "Invalid authority",
        "errors": {"authority": ["Invalid authority.", "-54"]},
    })
    assert "نامعتبر" in inquiry_msg


@pytest.mark.django_db
def test_zarinpal_requires_merchant_id(txn):
    gw = ZarinpalGateway()
    with pytest.raises(ValueError, match="merchant_id"):
        gw.create_payment(txn, {"sandbox": True, "simulate": True}, "http://cb/")
