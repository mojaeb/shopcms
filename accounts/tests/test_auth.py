"""Tests for OTP and JWT authentication."""

import pytest

from accounts.enums import OTPPurpose, RoleScope
from accounts.models import OTPCode, Role, User
from accounts.services.auth import AuthError, AuthService
from accounts.services.jwt import JWTService
from accounts.services.otp import OTPService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def setup_store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="Shop One", slug="shop1", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="localhost", is_primary=True)
    Role.objects.create(name="Customer", codename="customer", scope=RoleScope.STORE, is_system=True)
    return store


def _get_latest_otp(phone: str, purpose: str) -> str:
    otp = OTPCode.objects.filter(phone=phone, purpose=purpose).order_by("-created_at").first()
    return otp.code


@pytest.mark.django_db
def test_otp_send_and_verify_register(setup_store):
    otp_service = OTPService()
    result = otp_service.send_otp("09121111111", OTPPurpose.REGISTER, store=setup_store)
    assert result["phone"] == "09121111111"

    code = _get_latest_otp("09121111111", OTPPurpose.REGISTER)
    otp = otp_service.verify_otp("09121111111", code, OTPPurpose.REGISTER)
    assert otp.is_used


@pytest.mark.django_db
def test_register_flow(setup_store):
    otp_service = OTPService()
    auth_service = AuthService()

    otp_service.send_otp("09122222222", OTPPurpose.REGISTER, store=setup_store)
    code = _get_latest_otp("09122222222", OTPPurpose.REGISTER)

    user, tokens, membership = auth_service.register(
        phone="09122222222",
        code=code,
        store=setup_store,
        first_name="Sara",
        last_name="Ahmadi",
    )

    assert user.phone == "09122222222"
    assert user.full_name == "Sara Ahmadi"
    assert membership.role.codename == "customer"
    assert tokens.access_token
    assert tokens.refresh_token


@pytest.mark.django_db
def test_login_flow(setup_store):
    User.objects.create_user(phone="09123333333", phone_verified=True)
    otp_service = OTPService()
    auth_service = AuthService()

    otp_service.send_otp("09123333333", OTPPurpose.LOGIN)
    code = _get_latest_otp("09123333333", OTPPurpose.LOGIN)

    user2, tokens, membership = auth_service.login(
        phone="09123333333",
        code=code,
        store=setup_store,
    )

    assert user2.phone == "09123333333"
    assert membership.role.codename == "customer"
    assert tokens.access_token


@pytest.mark.django_db
def test_jwt_create_and_verify(setup_store):
    user = User.objects.create_user(phone="09124444444")
    jwt_service = JWTService()

    tokens = jwt_service.create_tokens(user.id, setup_store.id, "customer", 1)
    payload = jwt_service.verify_access_token(tokens.access_token)

    assert payload is not None
    assert payload["sub"] == str(user.id)
    assert payload["store_id"] == setup_store.id


@pytest.mark.django_db
def test_auth_api_register(client, setup_store):
    client.post(
        "/api/v1/auth/otp/send",
        data={"phone": "09125555555", "purpose": "register"},
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    code = _get_latest_otp("09125555555", OTPPurpose.REGISTER)

    response = client.post(
        "/api/v1/auth/otp/verify/register",
        data={
            "phone": "09125555555",
            "code": code,
            "first_name": "Reza",
            "last_name": "Karimi",
        },
        content_type="application/json",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["phone"] == "09125555555"
    assert data["role"] == "customer"
    assert "access_token" in data


@pytest.mark.django_db
def test_auth_api_me(client, setup_store):
    auth_service = AuthService()
    otp_service = OTPService()

    otp_service.send_otp("09126666666", OTPPurpose.REGISTER, store=setup_store)
    code = _get_latest_otp("09126666666", OTPPurpose.REGISTER)
    _, tokens, _ = auth_service.register("09126666666", code, setup_store)

    response = client.get(
        "/api/v1/auth/me",
        HTTP_AUTHORIZATION=f"Bearer {tokens.access_token}",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["phone"] == "09126666666"
    assert data["role"] == "customer"


@pytest.mark.django_db
def test_update_profile_service(setup_store):
    user = User.objects.create_user(
        phone="09127777777",
        first_name="Old",
        last_name="Name",
        email="old@example.com",
    )
    auth_service = AuthService()
    updated = auth_service.update_profile(
        user,
        first_name="New",
        last_name="Person",
        email="new@example.com",
    )
    assert updated.first_name == "New"
    assert updated.last_name == "Person"
    assert updated.email == "new@example.com"
    assert updated.full_name == "New Person"


@pytest.mark.django_db
def test_update_profile_rejects_invalid_email(setup_store):
    user = User.objects.create_user(phone="09128888888")
    auth_service = AuthService()
    with pytest.raises(AuthError, match="ایمیل"):
        auth_service.update_profile(user, email="not-an-email")


@pytest.mark.django_db
def test_auth_api_update_me(client, setup_store):
    auth_service = AuthService()
    otp_service = OTPService()

    otp_service.send_otp("09129999999", OTPPurpose.REGISTER, store=setup_store)
    code = _get_latest_otp("09129999999", OTPPurpose.REGISTER)
    user, tokens, _ = auth_service.register(
        "09129999999",
        code,
        setup_store,
        first_name="Ali",
        last_name="Rezaei",
    )

    response = client.patch(
        "/api/v1/auth/me",
        data={
            "first_name": "Maryam",
            "last_name": "Hosseini",
            "email": "maryam@example.com",
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {tokens.access_token}",
        HTTP_HOST="localhost",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Maryam"
    assert data["last_name"] == "Hosseini"
    assert data["email"] == "maryam@example.com"
    assert data["phone"] == "09129999999"

    user.refresh_from_db()
    assert user.first_name == "Maryam"
    assert user.email == "maryam@example.com"


@pytest.mark.django_db
def test_auth_api_update_me_requires_auth(client, setup_store):
    response = client.patch(
        "/api/v1/auth/me",
        data={"first_name": "X"},
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_phone_lookup_resolves_purpose(client, setup_store):
    response = client.post(
        "/api/v1/auth/phone/lookup",
        data={"phone": "09120001111"},
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is False
    assert data["purpose"] == "register"

    User.objects.create_user(phone="09120001111", phone_verified=True)
    response = client.post(
        "/api/v1/auth/phone/lookup",
        data={"phone": "09120001111"},
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["purpose"] == "login"


@pytest.mark.django_db
def test_otp_send_resolves_auth_purpose_alias(client, setup_store):
    """Legacy clients may send purpose=auth; resolve like phone lookup."""
    User.objects.create_user(phone="09120000000", phone_verified=True)

    response = client.post(
        "/api/v1/auth/otp/send",
        data={"phone": "09120000000", "purpose": "auth"},
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "09120000000"
    assert data["purpose"] == "login"

    response = client.post(
        "/api/v1/auth/otp/send",
        data={"phone": "09120000001", "purpose": "auth"},
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    assert response.json()["purpose"] == "register"


@pytest.mark.django_db
def test_otp_send_rejects_unknown_purpose(client, setup_store):
    response = client.post(
        "/api/v1/auth/otp/send",
        data={"phone": "09120000002", "purpose": "reset"},
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 400
    assert "هدف نامعتبر" in response.json()["detail"]


@pytest.mark.django_db
def test_otp_send_login_for_existing_phone(client, setup_store):
    User.objects.create_user(phone="09120000000", phone_verified=True)

    lookup = client.post(
        "/api/v1/auth/phone/lookup",
        data={"phone": "09120000000"},
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    assert lookup.status_code == 200
    assert lookup.json()["purpose"] == "login"

    response = client.post(
        "/api/v1/auth/otp/send",
        data={"phone": "09120000000", "purpose": "login"},
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "09120000000"
    assert data["purpose"] == "login"
