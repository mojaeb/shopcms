"""Account enumerations."""

from django.db import models


class RoleScope(models.TextChoices):
    PLATFORM = "platform", "پلتفرم"
    STORE = "store", "فروشگاه"


class OTPPurpose(models.TextChoices):
    LOGIN = "login", "ورود"
    REGISTER = "register", "ثبت‌نام"


class MembershipStatus(models.TextChoices):
    ACTIVE = "active", "فعال"
    INACTIVE = "inactive", "غیرفعال"
    SUSPENDED = "suspended", "معلق"


class TwoFactorMethod(models.TextChoices):
    TOTP = "totp", "TOTP"
