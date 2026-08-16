"""Permission checking utilities."""

from accounts.models import StoreMembership, User
from tenants.context import get_current_store
from tenants.models import Store


class PermissionService:
    """Check user permissions in store context."""

    def get_membership(self, user: User, store: Store | None = None) -> StoreMembership | None:
        store = store or get_current_store()
        if not user or not store:
            return None
        return (
            StoreMembership.objects.select_related("role")
            .prefetch_related("role__permissions")
            .filter(user=user, store=store, status="active")
            .first()
        )

    def get_staff_store_ids(self, user: User) -> set[int]:
        """Return store IDs where the user has an active staff role.

        Superusers are unrestricted elsewhere; this returns an empty set for them
        so callers should still check ``user.is_superuser`` first.
        """
        from dashboard.authentication_store import STAFF_ROLES

        if not user or not getattr(user, "is_authenticated", False):
            return set()
        return set(
            StoreMembership.objects.filter(
                user=user,
                status="active",
                role__codename__in=STAFF_ROLES,
            ).values_list("store_id", flat=True)
        )

    def can_manage_store(self, user: User, store: Store | None = None) -> bool:
        """True if user may manage the given store (staff membership or superuser)."""
        store = store or get_current_store()
        if not user or not getattr(user, "is_authenticated", False) or not store:
            return False
        if user.is_superuser:
            return True
        return self.is_store_staff(user, store)

    def has_permission(self, user: User, codename: str, store: Store | None = None) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        membership = self.get_membership(user, store)
        if not membership:
            return False

        if membership.role.codename == "store_admin":
            return True

        return membership.role.has_permission(codename)

    def has_role(self, user: User, role_codename: str, store: Store | None = None) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        membership = self.get_membership(user, store)
        return membership is not None and membership.role.codename == role_codename

    def is_store_admin(self, user: User, store: Store | None = None) -> bool:
        return self.has_role(user, "store_admin", store)

    def is_store_staff(self, user: User, store: Store | None = None) -> bool:
        """True if user is superuser or has an active staff role on the store."""
        from dashboard.authentication_store import STAFF_ROLES

        if not user or not getattr(user, "is_authenticated", False):
            return False
        if user.is_superuser:
            return True
        membership = self.get_membership(user, store)
        return bool(membership and membership.role.codename in STAFF_ROLES)

    def is_customer(self, user: User, store: Store | None = None) -> bool:
        return self.has_role(user, "customer", store)

    def get_user_roles(self, user: User, store: Store | None = None) -> list[str]:
        if user.is_superuser:
            return ["super_admin"]
        membership = self.get_membership(user, store)
        if membership:
            return [membership.role.codename]
        return []
