"""Two-factor authentication tests."""

import pytest

from accounts.enums import MembershipStatus, OTPPurpose, RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.auth import AuthService
from accounts.services.otp import OTPService
from accounts.services.two_factor import TwoFactorService
import pyotp
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="2FA Shop", slug="2fa-shop", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="2fa.local")
    Role.objects.create(codename="customer", name="Customer", scope=RoleScope.STORE, is_system=True)
    return store


@pytest.fixture
def staff_user(store):
    role = Role.objects.create(codename="store_admin", name="Admin", scope=RoleScope.STORE, is_system=True)
    user = User.objects.create_user(phone="09126660000", phone_verified=True, is_staff=True)
    membership = StoreMembership.objects.create(
        user=user, store=store, role=role, status=MembershipStatus.ACTIVE,
    )
    return user, membership


@pytest.mark.django_db
def test_totp_setup_and_enable(staff_user):
    user, _ = staff_user
    service = TwoFactorService()
    setup = service.setup_totp(user)
    code = pyotp.TOTP(setup["secret"]).now()
    backup_codes = service.enable_totp(user, code)
    assert service.is_enabled(user)
    assert len(backup_codes) == 8


@pytest.mark.django_db
def test_requires_2fa_for_staff(staff_user):
    user, membership = staff_user
    service = TwoFactorService()
    assert service.requires_2fa(user, membership) is False
    setup = service.setup_totp(user)
    service.enable_totp(user, pyotp.TOTP(setup["secret"]).now())
    assert service.requires_2fa(user, membership) is True


@pytest.mark.django_db
def test_login_challenge_flow(staff_user, store):
    user, membership = staff_user
    two_factor = TwoFactorService()
    setup = two_factor.setup_totp(user)
    two_factor.enable_totp(user, pyotp.TOTP(setup["secret"]).now())

    challenge = two_factor.create_challenge(user, store.id, membership.role.codename, membership.id)
    payload = two_factor.consume_challenge(challenge)
    assert payload["user_id"] == user.id

    assert two_factor.verify_code(user, pyotp.TOTP(setup["secret"]).now())

    auth_service = AuthService()
    _, tokens, _ = auth_service.complete_login(phone=user.phone, store=store)
    assert tokens.access_token
