"""Account models."""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from accounts.enums import MembershipStatus, OTPPurpose, RoleScope
from accounts.managers import UserManager
from core.models import TimeStampedModel
from tenants.models import Store


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Platform user with phone-based authentication."""

    phone = models.CharField(max_length=15, unique=True, verbose_name="موبایل")
    email = models.EmailField(blank=True, verbose_name="ایمیل")
    first_name = models.CharField(max_length=100, blank=True, verbose_name="نام")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="نام خانوادگی")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_staff = models.BooleanField(default=False, verbose_name="دسترسی ادمین")
    is_superuser = models.BooleanField(default=False, verbose_name="سوپرادمین")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="آخرین IP")
    phone_verified = models.BooleanField(default=False, verbose_name="موبایل تایید شده")

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ["-created_at"]

    def __str__(self):
        return self.phone

    @property
    def full_name(self) -> str:
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.phone


class Permission(TimeStampedModel):
    """Granular permission definition."""

    codename = models.CharField(max_length=100, unique=True, verbose_name="شناسه")
    name = models.CharField(max_length=200, verbose_name="نام")
    group = models.CharField(max_length=100, default="general", verbose_name="گروه")
    description = models.CharField(max_length=500, blank=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "دسترسی"
        verbose_name_plural = "دسترسی‌ها"
        ordering = ["group", "codename"]

    def __str__(self):
        return self.codename


class Role(TimeStampedModel):
    """Role with optional store scope."""

    name = models.CharField(max_length=100, verbose_name="نام")
    codename = models.CharField(max_length=50, unique=True, verbose_name="شناسه")
    scope = models.CharField(
        max_length=20,
        choices=RoleScope.choices,
        default=RoleScope.STORE,
        verbose_name="محدوده",
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="roles",
        verbose_name="دسترسی‌ها",
    )
    is_system = models.BooleanField(
        default=False,
        help_text="نقش‌های سیستمی قابل حذف نیستند",
        verbose_name="سیستمی",
    )
    description = models.CharField(max_length=500, blank=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "نقش"
        verbose_name_plural = "نقش‌ها"
        ordering = ["scope", "name"]

    def __str__(self):
        return self.name

    def has_permission(self, codename: str) -> bool:
        return self.permissions.filter(codename=codename).exists()


class StoreMembership(TimeStampedModel):
    """Links a user to a store with a specific role."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="کاربر",
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="فروشگاه",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="memberships",
        verbose_name="نقش",
    )
    status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
        verbose_name="وضعیت",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="ادمین اصلی فروشگاه",
        verbose_name="اصلی",
    )

    class Meta:
        verbose_name = "عضویت فروشگاه"
        verbose_name_plural = "عضویت‌های فروشگاه"
        unique_together = [("user", "store")]
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        return f"{self.user.phone} @ {self.store.slug} ({self.role.codename})"

    def save(self, *args, **kwargs):
        if self.is_primary and self.store_id:
            StoreMembership.objects.filter(store_id=self.store_id, is_primary=True).exclude(
                pk=self.pk
            ).update(is_primary=False)
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        return self.status == MembershipStatus.ACTIVE


class OTPCode(TimeStampedModel):
    """One-time password for login/register."""

    phone = models.CharField(max_length=15, verbose_name="موبایل")
    code = models.CharField(max_length=6, verbose_name="کد")
    purpose = models.CharField(
        max_length=20,
        choices=OTPPurpose.choices,
        verbose_name="هدف",
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="otp_codes",
        verbose_name="فروشگاه",
    )
    is_used = models.BooleanField(default=False, verbose_name="استفاده شده")
    expires_at = models.DateTimeField(verbose_name="انقضا")
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name="تلاش‌ها")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")

    class Meta:
        verbose_name = "کد OTP"
        verbose_name_plural = "کدهای OTP"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone", "purpose", "is_used"]),
        ]

    def __str__(self):
        return f"{self.phone} - {self.purpose}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired and self.attempts < 5


class UserSecuritySettings(TimeStampedModel):
    """Per-user security preferences including 2FA."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="security_settings",
        verbose_name="کاربر",
    )
    is_2fa_enabled = models.BooleanField(default=False, verbose_name="2FA فعال")
    totp_secret = models.CharField(max_length=64, blank=True, verbose_name="TOTP Secret")
    backup_codes = models.JSONField(default=list, blank=True, verbose_name="کدهای پشتیبان")

    class Meta:
        verbose_name = "تنظیمات امنیتی"
        verbose_name_plural = "تنظیمات امنیتی"

    def __str__(self):
        return f"Security settings for {self.user.phone}"


class UserDevice(TimeStampedModel):
    """Tracked login device/session."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="devices",
        verbose_name="کاربر",
    )
    device_key = models.CharField(max_length=64, verbose_name="کلید دستگاه")
    name = models.CharField(max_length=200, blank=True, verbose_name="نام")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    user_agent = models.CharField(max_length=500, blank=True, verbose_name="User Agent")
    last_seen = models.DateTimeField(auto_now=True, verbose_name="آخرین بازدید")
    is_trusted = models.BooleanField(default=False, verbose_name="مورد اعتماد")
    is_revoked = models.BooleanField(default=False, verbose_name="لغو شده")

    class Meta:
        verbose_name = "دستگاه کاربر"
        verbose_name_plural = "دستگاه‌های کاربر"
        unique_together = [("user", "device_key")]
        ordering = ["-last_seen"]

    def __str__(self):
        return f"{self.user.phone} - {self.name or self.device_key[:8]}"
