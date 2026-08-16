"""Assign and replace the primary store manager (store_admin + is_primary)."""

from __future__ import annotations

from django.db import transaction

from accounts.enums import MembershipStatus
from accounts.models import StoreMembership, User
from tenants.models import Store

MANAGER_ROLE_CODENAME = "store_admin"


class StoreManagerError(Exception):
    pass


class StoreManagerService:
    """One primary manager per store, visible and editable in CMS admin."""

    def get_primary_membership(self, store: Store) -> StoreMembership | None:
        if not store or not store.pk:
            return None
        return (
            StoreMembership.objects.select_related("user", "role")
            .filter(store=store, is_primary=True)
            .order_by("-updated_at")
            .first()
        )

    def get_primary_user(self, store: Store) -> User | None:
        membership = self.get_primary_membership(store)
        return membership.user if membership else None

    @transaction.atomic
    def assign_primary(
        self,
        store: Store,
        phone: str,
        first_name: str = "",
        last_name: str = "",
    ) -> StoreMembership:
        from accounts.services.auth import AuthService

        _user, membership = AuthService().create_store_admin(
            phone=phone,
            store=store,
            first_name=first_name,
            last_name=last_name,
            is_primary=True,
        )
        return membership

    @transaction.atomic
    def clear_primary(self, store: Store) -> None:
        StoreMembership.objects.filter(store=store, is_primary=True).update(is_primary=False)

    def sync_from_admin(self, store: Store, data: dict) -> StoreMembership | None:
        """Apply manager fields from StoreConfigForm. Empty phone clears primary."""
        phone = (data.get("store_manager_phone") or "").strip()
        if not phone:
            self.clear_primary(store)
            return None
        return self.assign_primary(
            store,
            phone=phone,
            first_name=(data.get("store_manager_first_name") or "").strip(),
            last_name=(data.get("store_manager_last_name") or "").strip(),
        )

    def admin_initial(self, store: Store) -> dict[str, str]:
        membership = self.get_primary_membership(store)
        if not membership:
            return {
                "store_manager_phone": "",
                "store_manager_first_name": "",
                "store_manager_last_name": "",
            }
        user = membership.user
        return {
            "store_manager_phone": user.phone,
            "store_manager_first_name": user.first_name,
            "store_manager_last_name": user.last_name,
        }
