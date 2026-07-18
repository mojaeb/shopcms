"""Store Admin service layer."""

import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.auth import AuthService
from tenants.models import Domain, Store, StorePlugin, StoreSetting
from tenants.services.cache import StoreCacheService
from taxes.services.tax import TaxService

logger = logging.getLogger(__name__)


class StoreAdminError(Exception):
    pass


class StoreAdminService:
    """Store-level management for store admin panel."""

    STAFF_ROLES = {"store_admin", "manager", "content", "products", "orders", "reports", "support"}

    def __init__(self):
        self.cache_service = StoreCacheService()
        self.auth_service = AuthService()

    def get_dashboard_stats(self, store: Store) -> dict:
        memberships = StoreMembership.objects.filter(store=store)
        customers = memberships.filter(role__codename="customer")
        staff = memberships.filter(role__codename__in=self.STAFF_ROLES)
        enabled_plugins = StorePlugin.objects.filter(store=store, is_enabled=True).count()
        order_stats = self._get_order_stats(store)

        return {
            "store_name": store.name,
            "store_slug": store.slug,
            "store_type": store.store_type,
            "status": store.status,
            "total_customers": customers.count(),
            "active_customers": customers.filter(status=MembershipStatus.ACTIVE).count(),
            "total_staff": staff.count(),
            "total_domains": Domain.objects.filter(store=store, is_active=True).count(),
            "enabled_plugins": enabled_plugins,
            "tax_enabled": store.tax_enabled,
            "currency": store.currency,
            "total_products": 0,
            "total_orders": order_stats["total_orders"],
            "pending_orders": order_stats["pending_orders"],
            "total_revenue": order_stats["total_revenue"],
            "orders_today": order_stats["orders_today"],
            "new_customers_today": customers.filter(
                created_at__date=timezone.now().date()
            ).count(),
        }

    def get_settings_overview(self, store: Store) -> dict:
        from tenants.services.theme_settings import ThemeSettingsService

        return {
            "general": {
                "name": store.name,
                "slug": store.slug,
                "store_type": store.store_type,
                "currency": store.currency,
                "timezone": store.timezone,
                "language": store.language,
                "theme_slug": store.effective_theme_slug,
            },
            "tax": {
                **TaxService().get_tax_settings(store),
            },
            "payment": self._get_group_settings(store, "payment"),
            "shipping": self._get_group_settings(store, "shipping"),
            "theme": ThemeSettingsService().get_theme_settings(store),
        }

    def update_theme_settings(self, store: Store, data: dict) -> dict:
        from tenants.services.theme_settings import ThemeSettingsService

        return ThemeSettingsService().update_theme_settings(store, data)

    @transaction.atomic
    def update_general_settings(self, store: Store, data: dict) -> dict:
        allowed = {"name", "currency", "timezone", "language"}
        for field in allowed:
            if field in data and data[field] is not None:
                setattr(store, field, data[field])
        store.save(update_fields=list(allowed & data.keys()) + ["updated_at"])
        self.cache_service.invalidate_store(store)
        return self.get_settings_overview(store)["general"]

    @transaction.atomic
    def update_tax_settings(self, store: Store, data: dict) -> dict:
        from taxes.services.tax import TaxService

        result = TaxService().update_tax_settings(store, data)
        self.cache_service.invalidate_store(store)
        return result

    def update_group_settings(self, store: Store, group: str, data: dict) -> dict:
        for key, value in data.items():
            StoreSetting.objects.update_or_create(
                store=store,
                group=group,
                key=key,
                defaults={"value": value, "value_type": "json"},
            )
        self.cache_service.invalidate_store(store)
        return self._get_group_settings(store, group)

    def list_users(self, store: Store, search: str = "", role: str | None = "customer"):
        qs = (
            StoreMembership.objects.select_related("user", "role")
            .filter(store=store)
            .order_by("-created_at")
        )
        if role and role != "all":
            qs = qs.filter(role__codename=role)
        if search:
            qs = qs.filter(
                Q(user__phone__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )
        return qs

    def list_team(self, store: Store):
        return (
            StoreMembership.objects.select_related("user", "role")
            .filter(store=store, role__codename__in=self.STAFF_ROLES)
            .order_by("-is_primary", "role__name")
        )

    def get_user_membership(self, store: Store, user_id: int) -> StoreMembership:
        return StoreMembership.objects.select_related("user", "role").get(
            store=store, user_id=user_id
        )

    @transaction.atomic
    def update_user_status(self, store: Store, user_id: int, status: str) -> StoreMembership:
        membership = self.get_user_membership(store, user_id)
        membership.status = status
        membership.save(update_fields=["status", "updated_at"])
        return membership

    @transaction.atomic
    def update_user_role(self, store: Store, user_id: int, role_codename: str) -> StoreMembership:
        role = Role.objects.get(codename=role_codename, scope=RoleScope.STORE)
        membership = self.get_user_membership(store, user_id)
        membership.role = role
        membership.save(update_fields=["role", "updated_at"])
        return membership

    @transaction.atomic
    def add_team_member(
        self,
        store: Store,
        phone: str,
        role_codename: str,
        first_name: str = "",
        last_name: str = "",
    ) -> StoreMembership:
        if role_codename == "store_admin":
            user, membership = self.auth_service.create_store_admin(
                phone=phone,
                store=store,
                first_name=first_name,
                last_name=last_name,
            )
            return membership

        from accounts.managers import UserManager

        phone = UserManager.normalize_phone(phone)
        role = Role.objects.get(codename=role_codename, scope=RoleScope.STORE)

        user, _ = User.objects.get_or_create(
            phone=phone,
            defaults={"first_name": first_name, "last_name": last_name, "phone_verified": True},
        )

        membership, _ = StoreMembership.objects.update_or_create(
            user=user,
            store=store,
            defaults={"role": role, "status": MembershipStatus.ACTIVE},
        )
        return membership

    def list_enabled_plugins(self, store: Store):
        return StorePlugin.objects.filter(store=store, is_enabled=True).select_related("plugin")

    def get_reports_summary(self, store: Store) -> dict:
        from reports.services.report import ReportService

        return ReportService().get_summary(store, days=30)

    def _get_order_stats(self, store: Store) -> dict:
        from orders.services.order import OrderService

        return OrderService().get_store_order_stats(store)

    def get_module_stub(self, module: str) -> dict:
        stubs = {
            "products": {
                "items": [],
                "total": 0,
                "message": "فاز محصولات - به زودی",
            },
            "orders": {
                "items": [],
                "total": 0,
                "message": "فاز سفارشات - به زودی",
            },
            "comments": {
                "items": [],
                "total": 0,
                "pending_moderation": 0,
                "message": "فاز کامنت‌ها - به زودی",
            },
            "blog": {
                "items": [],
                "total": 0,
                "message": "فاز وبلاگ - به زودی",
            },
        }
        return stubs.get(module, {"items": [], "total": 0})

    def _get_group_settings(self, store: Store, group: str) -> dict:
        settings = {}
        for item in StoreSetting.objects.filter(store=store, group=group):
            settings[item.key] = item.value
        return settings
