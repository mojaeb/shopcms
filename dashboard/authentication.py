"""Super Admin authentication - requires superuser."""

from ninja.errors import HttpError
from ninja.security import HttpBearer

from accounts.models import User
from accounts.services.jwt import JWTService


class SuperAdminAuth(HttpBearer):
    """Authenticate super admin via JWT + is_superuser check."""

    def authenticate(self, request, token):
        payload = JWTService().verify_access_token(token)
        if not payload:
            return None

        try:
            user = User.objects.get(pk=int(payload["sub"]), is_active=True, is_superuser=True)
        except User.DoesNotExist:
            return None

        request.jwt_payload = payload
        return user


super_admin_auth = SuperAdminAuth()
