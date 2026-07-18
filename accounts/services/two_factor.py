"""Two-factor authentication service (TOTP)."""

import hashlib
import logging
import secrets

import pyotp
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from accounts.enums import MembershipStatus
from accounts.models import StoreMembership, User, UserSecuritySettings
from dashboard.authentication_store import STAFF_ROLES

logger = logging.getLogger(__name__)

CHALLENGE_PREFIX = "shopcms:2fa:challenge:"
CHALLENGE_TTL = 300


class TwoFactorError(Exception):
    pass


class TwoFactorService:
    """Manage TOTP-based second factor for staff users."""

    def get_settings(self, user: User) -> UserSecuritySettings:
        settings_obj, _ = UserSecuritySettings.objects.get_or_create(user=user)
        return settings_obj

    def is_enabled(self, user: User) -> bool:
        return self.get_settings(user).is_2fa_enabled

    def requires_2fa(self, user: User, membership: StoreMembership | None) -> bool:
        if not self.is_enabled(user):
            return False
        if user.is_superuser or user.is_staff:
            return True
        if membership and membership.role.codename in STAFF_ROLES:
            return True
        return False

    def setup_totp(self, user: User) -> dict:
        security = self.get_settings(user)
        secret = pyotp.random_base32()
        security.totp_secret = secret
        security.is_2fa_enabled = False
        security.save(update_fields=["totp_secret", "is_2fa_enabled", "updated_at"])

        issuer = getattr(settings, "PLATFORM_NAME", "ShopCMS")
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=user.phone, issuer_name=issuer)
        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "issuer": issuer,
        }

    def enable_totp(self, user: User, code: str) -> list[str]:
        security = self.get_settings(user)
        if not security.totp_secret:
            raise TwoFactorError("ابتدا 2FA را راه‌اندازی کنید")
        if not self._verify_code(security.totp_secret, code):
            raise TwoFactorError("کد 2FA نامعتبر است")

        backup_codes = [secrets.token_hex(4) for _ in range(8)]
        security.is_2fa_enabled = True
        security.backup_codes = backup_codes
        security.save(update_fields=["is_2fa_enabled", "backup_codes", "updated_at"])
        return backup_codes

    def disable_totp(self, user: User, code: str) -> None:
        security = self.get_settings(user)
        if security.is_2fa_enabled and not self.verify_code(user, code):
            raise TwoFactorError("کد 2FA نامعتبر است")
        security.is_2fa_enabled = False
        security.totp_secret = ""
        security.backup_codes = []
        security.save(update_fields=["is_2fa_enabled", "totp_secret", "backup_codes", "updated_at"])

    def verify_code(self, user: User, code: str) -> bool:
        security = self.get_settings(user)
        if not security.totp_secret:
            return False
        if self._verify_code(security.totp_secret, code):
            return True
        if code in security.backup_codes:
            security.backup_codes = [item for item in security.backup_codes if item != code]
            security.save(update_fields=["backup_codes", "updated_at"])
            return True
        return False

    def create_challenge(
        self,
        user: User,
        store_id: int | None,
        role_codename: str | None,
        membership_id: int | None,
    ) -> str:
        token = secrets.token_urlsafe(32)
        cache.set(
            f"{CHALLENGE_PREFIX}{token}",
            {
                "user_id": user.id,
                "store_id": store_id,
                "role": role_codename,
                "membership_id": membership_id,
                "created_at": timezone.now().isoformat(),
            },
            CHALLENGE_TTL,
        )
        return token

    def consume_challenge(self, token: str) -> dict:
        key = f"{CHALLENGE_PREFIX}{token}"
        payload = cache.get(key)
        if not payload:
            raise TwoFactorError("چالش 2FA منقضی یا نامعتبر است")
        cache.delete(key)
        return payload

    def _verify_code(self, secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
