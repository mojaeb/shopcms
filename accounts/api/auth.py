"""Authentication API endpoints."""

from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.authentication import jwt_auth
from accounts.enums import MembershipStatus, OTPPurpose
from accounts.models import User
from accounts.services.auth import AuthError, AuthService
from accounts.services.device import DeviceService
from accounts.services.otp import OTPError, OTPInvalidError, OTPRateLimitError, OTPService
from accounts.services.permissions import PermissionService
from accounts.services.two_factor import TwoFactorError, TwoFactorService
from core.enums import AuditAction, AuditOutcome
from core.security.throttling import AuthRefreshRateThrottle, OTPSendRateThrottle
from core.services.audit import AuditService
from core.utils.request import get_client_ip
from tenants.context import get_current_store

router = Router()
auth_service = AuthService()
otp_service = OTPService()
permission_service = PermissionService()
two_factor_service = TwoFactorService()
device_service = DeviceService()
audit_service = AuditService()


class OTPSendSchema(Schema):
    phone: str
    purpose: str


class OTPVerifySchema(Schema):
    phone: str
    code: str


class RegisterSchema(Schema):
    phone: str
    code: str
    first_name: str = ""
    last_name: str = ""


class RefreshTokenSchema(Schema):
    refresh_token: str


class LogoutSchema(Schema):
    refresh_token: str = ""


class TwoFAEnableSchema(Schema):
    code: str


class TwoFAVerifySchema(Schema):
    challenge_token: str
    code: str


class UserSchema(Schema):
    id: int
    phone: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone_verified: bool
    is_superuser: bool


class TokenResponseSchema(Schema):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserSchema
    role: str | None = None
    store_id: int | None = None


class TwoFAChallengeSchema(Schema):
    requires_2fa: bool = True
    challenge_token: str
    expires_in: int = 300


class MeResponseSchema(Schema):
    user: UserSchema
    role: str | None = None
    roles: list[str]
    store_id: int | None = None
    permissions: list[str]
    is_2fa_enabled: bool = False


class DeviceSchema(Schema):
    id: int
    name: str
    ip_address: str | None
    user_agent: str
    last_seen: str
    is_trusted: bool


def _user_to_schema(user) -> UserSchema:
    return UserSchema(
        id=user.id,
        phone=user.phone,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        phone_verified=user.phone_verified,
        is_superuser=user.is_superuser,
    )


def _resolve_membership(user, store):
    if not store:
        return None
    return (
        user.memberships.select_related("role")
        .filter(store=store, status=MembershipStatus.ACTIVE)
        .first()
    )


def _token_response(user, tokens, membership, store):
    return TokenResponseSchema(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=_user_to_schema(user),
        role=membership.role.codename if membership else None,
        store_id=store.id if store else None,
    )


@router.post("/otp/send", throttle=OTPSendRateThrottle())
def send_otp(request, payload: OTPSendSchema):
    """Send OTP code for login or register."""
    if payload.purpose not in (OTPPurpose.LOGIN, OTPPurpose.REGISTER):
        raise HttpError(400, "هدف نامعتبر است")

    store = get_current_store() or getattr(request, "store", None)

    if payload.purpose == OTPPurpose.REGISTER and not store:
        raise HttpError(400, "فروشگاه مشخص نیست")

    try:
        result = otp_service.send_otp(
            phone=payload.phone,
            purpose=payload.purpose,
            store=store,
            ip_address=get_client_ip(request),
        )
        audit_service.log(
            AuditAction.OTP_SEND,
            request=request,
            store=store,
            outcome=AuditOutcome.SUCCESS,
            metadata={"phone": result["phone"], "purpose": payload.purpose},
        )
        return result
    except OTPRateLimitError as e:
        audit_service.log(
            AuditAction.RATE_LIMITED,
            request=request,
            store=store,
            outcome=AuditOutcome.BLOCKED,
            metadata={"scope": "otp_send"},
        )
        raise HttpError(429, str(e))
    except OTPError as e:
        audit_service.log(
            AuditAction.OTP_FAILED,
            request=request,
            store=store,
            outcome=AuditOutcome.FAILURE,
            metadata={"reason": str(e)},
        )
        raise HttpError(400, str(e))


@router.post("/otp/verify/login", response={200: TokenResponseSchema, 202: TwoFAChallengeSchema})
def verify_login(request, payload: OTPVerifySchema):
    """Verify OTP and login. Staff with 2FA receive a challenge token."""
    store = get_current_store() or getattr(request, "store", None)

    try:
        otp_service.verify_otp(payload.phone, payload.code, OTPPurpose.LOGIN)
    except OTPInvalidError as e:
        audit_service.log(
            AuditAction.OTP_FAILED,
            request=request,
            store=store,
            outcome=AuditOutcome.FAILURE,
            metadata={"phone": payload.phone},
        )
        raise HttpError(400, str(e))

    phone = otp_service._normalize_phone(payload.phone)
    try:
        user = User.objects.get(phone=phone, is_active=True)
    except User.DoesNotExist:
        raise HttpError(404, "کاربر یافت نشد")

    membership = _resolve_membership(user, store)
    if two_factor_service.requires_2fa(user, membership):
        store_id = store.id if store else None
        role = membership.role.codename if membership else None
        membership_id = membership.id if membership else None
        challenge = two_factor_service.create_challenge(user, store_id, role, membership_id)
        return 202, TwoFAChallengeSchema(challenge_token=challenge)

    user, tokens, membership = auth_service.complete_login(
        phone=phone,
        store=store,
        ip_address=get_client_ip(request),
        create_session=True,
        request=request,
    )
    return _token_response(user, tokens, membership, store)


@router.post("/2fa/verify", response=TokenResponseSchema)
def verify_two_factor(request, payload: TwoFAVerifySchema):
    """Complete staff login after 2FA challenge."""
    store = get_current_store() or getattr(request, "store", None)
    try:
        challenge = two_factor_service.consume_challenge(payload.challenge_token)
        user = User.objects.get(pk=challenge["user_id"], is_active=True)
        if not two_factor_service.verify_code(user, payload.code):
            audit_service.log(
                AuditAction.TWO_FA_VERIFY,
                request=request,
                user=user,
                store=store,
                outcome=AuditOutcome.FAILURE,
            )
            raise HttpError(400, "کد 2FA نامعتبر است")
    except TwoFactorError as e:
        raise HttpError(400, str(e)) from e
    except User.DoesNotExist:
        raise HttpError(404, "کاربر یافت نشد")

    user, tokens, membership = auth_service.complete_login(
        phone=user.phone,
        store=store,
        ip_address=get_client_ip(request),
        create_session=True,
        request=request,
    )
    audit_service.log(
        AuditAction.TWO_FA_VERIFY,
        request=request,
        user=user,
        store=store,
        outcome=AuditOutcome.SUCCESS,
    )
    return _token_response(user, tokens, membership, store)


@router.post("/otp/verify/register", response=TokenResponseSchema)
def verify_register(request, payload: RegisterSchema):
    """Verify OTP and register new customer."""
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")

    try:
        user, tokens, membership = auth_service.register(
            phone=payload.phone,
            code=payload.code,
            store=store,
            first_name=payload.first_name,
            last_name=payload.last_name,
            ip_address=get_client_ip(request),
            create_session=True,
            request=request,
        )
        return _token_response(user, tokens, membership, store)
    except OTPInvalidError as e:
        raise HttpError(400, str(e))
    except AuthError as e:
        raise HttpError(400, str(e))


@router.post("/token/refresh", response=TokenResponseSchema, throttle=AuthRefreshRateThrottle())
def refresh_token(request, payload: RefreshTokenSchema):
    """Refresh access token using refresh token."""
    from accounts.services.jwt import JWTService

    tokens = auth_service.refresh_tokens(payload.refresh_token)
    if not tokens:
        audit_service.log(
            AuditAction.TOKEN_REFRESH,
            request=request,
            outcome=AuditOutcome.FAILURE,
        )
        raise HttpError(401, "توکن نامعتبر است")

    jwt_payload = JWTService().verify_access_token(tokens.access_token)
    user = User.objects.get(pk=int(jwt_payload["sub"]))
    audit_service.log(
        AuditAction.TOKEN_REFRESH,
        request=request,
        user=user,
        outcome=AuditOutcome.SUCCESS,
    )

    return TokenResponseSchema(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=_user_to_schema(user),
        role=jwt_payload.get("role"),
        store_id=jwt_payload.get("store_id"),
    )


@router.post("/logout")
def logout(request, payload: LogoutSchema):
    """Logout and blacklist tokens."""
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    access_token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else None

    auth_service.logout(
        request=request,
        access_token=access_token,
        refresh_token=payload.refresh_token or None,
    )
    return {"detail": "خروج موفق"}


@router.get("/me", response=MeResponseSchema, auth=jwt_auth)
def me(request):
    """Get current authenticated user profile."""
    user = request.auth
    store = get_current_store() or getattr(request, "store", None)

    membership = permission_service.get_membership(user, store)
    permissions = []
    if user.is_superuser:
        permissions = ["*"]
    elif membership:
        if membership.role.codename == "store_admin":
            permissions = ["*"]
        else:
            permissions = list(membership.role.permissions.values_list("codename", flat=True))

    return MeResponseSchema(
        user=_user_to_schema(user),
        role=membership.role.codename if membership else getattr(request, "role", None),
        roles=permission_service.get_user_roles(user, store),
        store_id=store.id if store else getattr(request, "store_id", None),
        permissions=permissions,
        is_2fa_enabled=two_factor_service.is_enabled(user),
    )


@router.post("/2fa/setup", auth=jwt_auth)
def setup_two_factor(request):
    """Generate TOTP secret for the current user."""
    return two_factor_service.setup_totp(request.auth)


@router.post("/2fa/enable", auth=jwt_auth)
def enable_two_factor(request, payload: TwoFAEnableSchema):
    """Enable 2FA after verifying a TOTP code."""
    try:
        backup_codes = two_factor_service.enable_totp(request.auth, payload.code)
    except TwoFactorError as e:
        raise HttpError(400, str(e)) from e
    audit_service.log(
        AuditAction.TWO_FA_ENABLE,
        request=request,
        user=request.auth,
        outcome=AuditOutcome.SUCCESS,
    )
    return {"status": "ok", "backup_codes": backup_codes}


@router.post("/2fa/disable", auth=jwt_auth)
def disable_two_factor(request, payload: TwoFAEnableSchema):
    """Disable 2FA for the current user."""
    try:
        two_factor_service.disable_totp(request.auth, payload.code)
    except TwoFactorError as e:
        raise HttpError(400, str(e)) from e
    audit_service.log(
        AuditAction.TWO_FA_DISABLE,
        request=request,
        user=request.auth,
        outcome=AuditOutcome.SUCCESS,
    )
    return {"status": "ok"}


@router.get("/devices", response=list[DeviceSchema], auth=jwt_auth)
def list_devices(request):
    devices = device_service.list_devices(request.auth)
    return [
        DeviceSchema(
            id=device.id,
            name=device.name,
            ip_address=device.ip_address,
            user_agent=device.user_agent,
            last_seen=device.last_seen.isoformat(),
            is_trusted=device.is_trusted,
        )
        for device in devices
    ]


@router.delete("/devices/{device_id}", auth=jwt_auth)
def revoke_device(request, device_id: int):
    if not device_service.revoke_device(request.auth, device_id):
        raise HttpError(404, "دستگاه یافت نشد")
    audit_service.log(
        AuditAction.DEVICE_REVOKE,
        request=request,
        user=request.auth,
        outcome=AuditOutcome.SUCCESS,
        resource_type="device",
        resource_id=device_id,
    )
    return {"status": "ok"}
