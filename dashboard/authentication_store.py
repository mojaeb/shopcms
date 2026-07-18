"""Store Admin authentication and permission checks."""

from functools import wraps

from ninja.errors import HttpError
from ninja.security import HttpBearer

from accounts.models import User
from accounts.services.jwt import JWTService
from accounts.services.permissions import PermissionService
from tenants.context import get_current_store

STAFF_ROLES = {
    "store_admin",
    "manager",
    "content",
    "products",
    "orders",
    "reports",
    "support",
}


class StoreAdminAuth(HttpBearer):
    """Authenticate store staff via JWT with store context."""

    def __init__(self, permission: str | None = None):
        self.permission = permission
        self.permission_service = PermissionService()

    def authenticate(self, request, token):
        payload = JWTService().verify_access_token(token)
        if not payload:
            return None

        try:
            user = User.objects.get(pk=int(payload["sub"]), is_active=True)
        except User.DoesNotExist:
            return None

        store = get_current_store() or getattr(request, "store", None)
        if not store:
            return None

        if user.is_superuser:
            request.store = store
            request.membership = None
            request.jwt_payload = payload
            request.role = "super_admin"
            if self.permission and not self._check_super_permission():
                return None
            return user

        jwt_store_id = payload.get("store_id")
        if jwt_store_id and int(jwt_store_id) != store.id:
            return None

        membership = self.permission_service.get_membership(user, store)
        if not membership:
            return None

        if membership.role.codename not in STAFF_ROLES:
            return None

        if self.permission and not self.permission_service.has_permission(user, self.permission, store):
            return None

        request.store = store
        request.membership = membership
        request.jwt_payload = payload
        request.role = membership.role.codename
        return user

    def _check_super_permission(self) -> bool:
        return self.permission is None


store_admin_auth = StoreAdminAuth()
store_products_auth = StoreAdminAuth(permission="products.view")
store_orders_auth = StoreAdminAuth(permission="orders.view")
store_reports_auth = StoreAdminAuth(permission="reports.view")
store_content_auth = StoreAdminAuth(permission="blog.manage")
store_comments_auth = StoreAdminAuth(permission="comments.moderate")
store_files_auth = StoreAdminAuth(permission="files.manage")
store_settings_auth = StoreAdminAuth(permission="settings.manage")
store_backup_auth = StoreAdminAuth(permission="backup.manage")
store_security_auth = StoreAdminAuth(permission="security.view")


def require_store_admin(func):
    """Decorator to ensure user is store_admin for the current store."""

    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.auth.is_superuser:
            return func(request, *args, **kwargs)
        membership = getattr(request, "membership", None)
        if not membership or membership.role.codename != "store_admin":
            raise HttpError(403, "دسترسی ادمین فروشگاه لازم است")
        return func(request, *args, **kwargs)

    return wrapper
