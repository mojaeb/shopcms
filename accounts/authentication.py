"""Django Ninja JWT authentication."""

from ninja.security import HttpBearer

from accounts.models import User
from accounts.services.jwt import JWTService


class JWTAuth(HttpBearer):
    """Authenticate requests via Bearer JWT token."""

    def authenticate(self, request, token):
        payload = JWTService().verify_access_token(token)
        if not payload:
            return None

        try:
            user = User.objects.get(pk=int(payload["sub"]), is_active=True)
        except User.DoesNotExist:
            return None

        request.jwt_payload = payload
        request.store_id = payload.get("store_id")
        request.role = payload.get("role")
        return user


jwt_auth = JWTAuth()
