"""Authentication service - login, register, session."""

import logging

from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.db import transaction

from accounts.enums import MembershipStatus, OTPPurpose, RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.device import DeviceService
from accounts.services.jwt import JWTService, TokenPair
from accounts.services.otp import OTPInvalidError, OTPService
from accounts.services.two_factor import TwoFactorService
from core.services.audit import AuditService
from tenants.models import Store

logger = logging.getLogger(__name__)


class AuthError(Exception):
    pass


class AuthService:
    """Orchestrate OTP auth, registration, and token issuance."""

    def __init__(self):
        self.otp_service = OTPService()
        self.jwt_service = JWTService()
        self.two_factor_service = TwoFactorService()
        self.device_service = DeviceService()
        self.audit_service = AuditService()

    def _get_customer_role(self) -> Role:
        role, _ = Role.objects.get_or_create(
            codename="customer",
            defaults={
                "name": "مشتری",
                "scope": RoleScope.STORE,
                "is_system": True,
            },
        )
        return role

    def _get_store_admin_role(self) -> Role:
        role, _ = Role.objects.get_or_create(
            codename="store_admin",
            defaults={
                "name": "ادمین فروشگاه",
                "scope": RoleScope.STORE,
                "is_system": True,
            },
        )
        return role

    @transaction.atomic
    def register(
        self,
        phone: str,
        code: str,
        store: Store,
        first_name: str = "",
        last_name: str = "",
        ip_address: str | None = None,
        create_session: bool = False,
        request=None,
    ) -> tuple[User, TokenPair, StoreMembership]:
        self.otp_service.verify_otp(phone, code, OTPPurpose.REGISTER)

        user = User.objects.create(
            phone=self.otp_service._normalize_phone(phone),
            first_name=first_name,
            last_name=last_name,
            phone_verified=True,
            last_login_ip=ip_address,
        )

        customer_role = self._get_customer_role()
        membership = StoreMembership.objects.create(
            user=user,
            store=store,
            role=customer_role,
            status=MembershipStatus.ACTIVE,
        )

        tokens = self.jwt_service.create_tokens(
            user.id,
            store.id,
            customer_role.codename,
            membership.id,
        )

        if store and request:
            from carts.services.cart import CartService

            CartService().merge_on_login(store, request, user)
            self.device_service.record_login(request, user)
            self.audit_service.log_register(request, user, store)

        if create_session and request:
            django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        logger.info("User registered: %s for store %s", user.phone, store.slug)
        return user, tokens, membership

    def login(
        self,
        phone: str,
        code: str,
        store: Store | None = None,
        ip_address: str | None = None,
        create_session: bool = False,
        request=None,
    ) -> tuple[User, TokenPair, StoreMembership | None]:
        self.otp_service.verify_otp(phone, code, OTPPurpose.LOGIN)
        return self.complete_login(
            phone=phone,
            store=store,
            ip_address=ip_address,
            create_session=create_session,
            request=request,
        )

    def complete_login(
        self,
        phone: str,
        store: Store | None = None,
        ip_address: str | None = None,
        create_session: bool = False,
        request=None,
    ) -> tuple[User, TokenPair, StoreMembership | None]:
        phone = self.otp_service._normalize_phone(phone)
        user = User.objects.get(phone=phone, is_active=True)

        if ip_address:
            user.last_login_ip = ip_address
            user.save(update_fields=["last_login_ip"])

        membership = None
        role_codename = None
        membership_id = None
        store_id = None

        if store:
            membership = (
                StoreMembership.objects.select_related("role")
                .filter(user=user, store=store, status=MembershipStatus.ACTIVE)
                .first()
            )
            if not membership and not user.is_superuser:
                customer_role = self._get_customer_role()
                membership = StoreMembership.objects.create(
                    user=user,
                    store=store,
                    role=customer_role,
                    status=MembershipStatus.ACTIVE,
                )

            if membership:
                role_codename = membership.role.codename
                membership_id = membership.id
                store_id = store.id

        tokens = self.jwt_service.create_tokens(
            user.id,
            store_id,
            role_codename,
            membership_id,
        )

        if store and request:
            from carts.services.cart import CartService

            CartService().merge_on_login(store, request, user)
            self.device_service.record_login(request, user)
            self.audit_service.log_login(request, user, store)

        if create_session and request:
            django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        logger.info("User logged in: %s", user.phone)
        return user, tokens, membership

    def logout(self, request=None, access_token: str | None = None, refresh_token: str | None = None):
        user = getattr(request, "user", None) if request else None
        if access_token:
            self.jwt_service.blacklist_token(access_token)
        if refresh_token:
            self.jwt_service.blacklist_token(refresh_token)
        if request:
            store = getattr(request, "store", None)
            if user and getattr(user, "is_authenticated", False):
                self.audit_service.log_logout(request, user, store)
            django_logout(request)

    def refresh_tokens(self, refresh_token: str) -> TokenPair | None:
        return self.jwt_service.refresh_access_token(refresh_token)

    @transaction.atomic
    def create_store_admin(
        self,
        phone: str,
        store: Store,
        first_name: str = "",
        last_name: str = "",
        is_primary: bool = False,
    ) -> tuple[User, StoreMembership]:
        """Create or assign a store admin (used by super admin)."""
        from accounts.managers import UserManager

        phone = UserManager.normalize_phone(phone)

        user, _created = User.objects.get_or_create(
            phone=phone,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "phone_verified": True,
                "is_staff": True,
            },
        )

        update_fields: list[str] = []
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            update_fields.append("first_name")
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            update_fields.append("last_name")
        if not user.is_staff:
            user.is_staff = True
            update_fields.append("is_staff")
        if not user.phone_verified:
            user.phone_verified = True
            update_fields.append("phone_verified")
        if not user.is_active:
            user.is_active = True
            update_fields.append("is_active")
        if update_fields:
            user.save(update_fields=update_fields)

        if is_primary:
            StoreMembership.objects.filter(store=store, is_primary=True).exclude(user=user).update(
                is_primary=False
            )

        admin_role = self._get_store_admin_role()
        membership, _ = StoreMembership.objects.update_or_create(
            user=user,
            store=store,
            defaults={
                "role": admin_role,
                "status": MembershipStatus.ACTIVE,
                "is_primary": is_primary,
            },
        )

        return user, membership

    def update_profile(
        self,
        user: User,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
    ) -> User:
        """Update editable profile fields for the authenticated user."""
        update_fields: list[str] = []

        if first_name is not None:
            user.first_name = first_name.strip()[:100]
            update_fields.append("first_name")
        if last_name is not None:
            user.last_name = last_name.strip()[:100]
            update_fields.append("last_name")
        if email is not None:
            email = email.strip()
            if email:
                from django.core.exceptions import ValidationError
                from django.core.validators import validate_email

                try:
                    validate_email(email)
                except ValidationError as e:
                    raise AuthError("ایمیل معتبر نیست") from e
            user.email = email
            update_fields.append("email")

        if update_fields:
            update_fields.append("updated_at")
            user.save(update_fields=update_fields)

        return user
