"""JWT token service."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)
BLACKLIST_PREFIX = "jwt:blacklist:"


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900


class JWTService:
    """Create and validate JWT access/refresh tokens."""

    @property
    def secret_key(self) -> str:
        return settings.SECRET_KEY

    def _encode(self, payload: dict, lifetime: timedelta) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            **payload,
            "iat": now,
            "exp": now + lifetime,
        }
        return jwt.encode(payload, self.secret_key, algorithm=JWT_ALGORITHM)

    def create_tokens(
        self,
        user_id: int,
        store_id: int | None = None,
        role: str | None = None,
        membership_id: int | None = None,
    ) -> TokenPair:
        base_payload: dict[str, Any] = {
            "sub": str(user_id),
            "type": "access",
        }
        if store_id:
            base_payload["store_id"] = store_id
        if role:
            base_payload["role"] = role
        if membership_id:
            base_payload["membership_id"] = membership_id

        access_token = self._encode(base_payload, ACCESS_TOKEN_LIFETIME)

        refresh_payload = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": f"{user_id}-{datetime.now(timezone.utc).timestamp()}",
        }
        if store_id:
            refresh_payload["store_id"] = store_id

        refresh_token = self._encode(refresh_payload, REFRESH_TOKEN_LIFETIME)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(ACCESS_TOKEN_LIFETIME.total_seconds()),
        )

    def decode(self, token: str) -> dict:
        return jwt.decode(token, self.secret_key, algorithms=[JWT_ALGORITHM])

    def verify_access_token(self, token: str) -> dict | None:
        try:
            if self.is_blacklisted(token):
                return None
            payload = self.decode(token)
            if payload.get("type") != "access":
                return None
            return payload
        except jwt.PyJWTError as e:
            logger.debug("Invalid access token: %s", e)
            return None

    def verify_refresh_token(self, token: str) -> dict | None:
        try:
            if self.is_blacklisted(token):
                return None
            payload = self.decode(token)
            if payload.get("type") != "refresh":
                return None
            return payload
        except jwt.PyJWTError as e:
            logger.debug("Invalid refresh token: %s", e)
            return None

    def blacklist_token(self, token: str) -> None:
        try:
            payload = self.decode(token)
            exp = payload.get("exp")
            if exp:
                ttl = int(exp - datetime.now(timezone.utc).timestamp())
                if ttl > 0:
                    cache.set(f"{BLACKLIST_PREFIX}{token[:32]}", True, ttl)
        except jwt.PyJWTError:
            pass

    def is_blacklisted(self, token: str) -> bool:
        return cache.get(f"{BLACKLIST_PREFIX}{token[:32]}") is not None

    def refresh_access_token(self, refresh_token: str) -> TokenPair | None:
        payload = self.verify_refresh_token(refresh_token)
        if not payload:
            return None

        user_id = int(payload["sub"])
        store_id = payload.get("store_id")

        role = None
        membership_id = None
        if store_id:
            from accounts.models import StoreMembership

            membership = (
                StoreMembership.objects.select_related("role")
                .filter(user_id=user_id, store_id=store_id, status="active")
                .first()
            )
            if membership:
                role = membership.role.codename
                membership_id = membership.id

        return self.create_tokens(user_id, store_id, role, membership_id)
