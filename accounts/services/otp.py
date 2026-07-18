"""OTP generation and verification service."""

import logging
import random
import string
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from accounts.enums import OTPPurpose
from accounts.models import OTPCode, User
from accounts.managers import UserManager
from core.services.rate_limit import RateLimitExceeded, RateLimitService
from tenants.models import Store

logger = logging.getLogger(__name__)

OTP_LENGTH = 5
OTP_EXPIRY_MINUTES = 2
OTP_RATE_LIMIT_SECONDS = 60
# Max OTP sends per phone within the window (1 in production; higher when fixed OTP / override)
OTP_RATE_LIMIT_COUNT = 1


class OTPError(Exception):
    pass


class OTPRateLimitError(OTPError):
    def __init__(self, message: str = "تعداد درخواست بیش از حد مجاز است", retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class OTPInvalidError(OTPError):
    pass


class OTPService:
    """Handle OTP lifecycle for login and registration."""

    def __init__(self):
        self.user_manager = UserManager()
        self.rate_limiter = RateLimitService()

    def _normalize_phone(self, phone: str) -> str:
        return self.user_manager.normalize_phone(phone)

    def _generate_code(self) -> str:
        if getattr(settings, "OTP_USE_FIXED_CODE", False):
            return settings.OTP_FIXED_CODE
        return "".join(random.choices(string.digits, k=OTP_LENGTH))

    def _rate_limit_params(self) -> tuple[int, int]:
        window = int(getattr(settings, "OTP_RATE_LIMIT_SECONDS", OTP_RATE_LIMIT_SECONDS))
        limit = int(getattr(settings, "OTP_RATE_LIMIT_COUNT", OTP_RATE_LIMIT_COUNT))
        return max(limit, 1), max(window, 1)

    def _check_rate_limit(self, phone: str) -> None:
        limit, window = self._rate_limit_params()
        try:
            self.rate_limiter.hit(
                "otp_send",
                phone,
                limit=limit,
                window_seconds=window,
            )
        except RateLimitExceeded as exc:
            wait = exc.retry_after or window
            raise OTPRateLimitError(
                f"لطفاً حدود {wait} ثانیه صبر کنید و دوباره کد بخواهید.",
                retry_after=wait,
            ) from exc

    def reset_send_limit(self, phone: str) -> None:
        phone = self._normalize_phone(phone)
        self.rate_limiter.reset("otp_send", phone)

    def _send_sms(self, phone: str, code: str, store: Store | None = None) -> None:
        from notifications.services.notification import NotificationError, NotificationService

        try:
            NotificationService().send_otp_sms(phone, code, store=store)
        except NotificationError:
            logger.exception("Failed to send OTP SMS to %s", phone)
            raise OTPError("ارسال پیامک با خطا مواجه شد")

    def send_otp(
        self,
        phone: str,
        purpose: str,
        store: Store | None = None,
        ip_address: str | None = None,
    ) -> dict:
        phone = self._normalize_phone(phone)

        if purpose == OTPPurpose.LOGIN:
            if not User.objects.filter(phone=phone, is_active=True).exists():
                raise OTPError("کاربری با این شماره یافت نشد")

        if purpose == OTPPurpose.REGISTER:
            if User.objects.filter(phone=phone).exists():
                raise OTPError("این شماره قبلاً ثبت شده است")

        self._check_rate_limit(phone)

        OTPCode.objects.filter(
            phone=phone,
            purpose=purpose,
            is_used=False,
        ).update(is_used=True)

        code = self._generate_code()
        otp = OTPCode.objects.create(
            phone=phone,
            code=code,
            purpose=purpose,
            store=store,
            expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
            ip_address=ip_address,
        )

        self._send_sms(phone, code, store=store)

        return {
            "phone": phone,
            "purpose": purpose,
            "expires_in": OTP_EXPIRY_MINUTES * 60,
            "otp_id": otp.id,
        }

    def verify_otp(
        self,
        phone: str,
        code: str,
        purpose: str,
    ) -> OTPCode:
        phone = self._normalize_phone(phone)

        otp = (
            OTPCode.objects.filter(
                phone=phone,
                purpose=purpose,
                is_used=False,
            )
            .order_by("-created_at")
            .first()
        )

        if not otp:
            raise OTPInvalidError("کد یافت نشد")

        if otp.is_expired:
            raise OTPInvalidError("کد منقضی شده است")

        otp.attempts += 1
        otp.save(update_fields=["attempts"])

        if otp.attempts > 5:
            otp.is_used = True
            otp.save(update_fields=["is_used"])
            raise OTPInvalidError("تعداد تلاش‌ها بیش از حد مجاز است")

        if otp.code != code:
            raise OTPInvalidError("کد نادرست است")

        otp.is_used = True
        otp.save(update_fields=["is_used"])
        self.reset_send_limit(phone)
        return otp
