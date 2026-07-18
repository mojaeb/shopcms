"""Core application enums."""

from django.db import models


class BackupScope(models.TextChoices):
    STORE = "store", "Store"
    PLATFORM = "platform", "Platform"


class BackupStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class AuditAction(models.TextChoices):
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    REGISTER = "register", "Register"
    OTP_SEND = "otp_send", "OTP Send"
    OTP_FAILED = "otp_failed", "OTP Failed"
    TOKEN_REFRESH = "token_refresh", "Token Refresh"
    TWO_FA_VERIFY = "two_fa_verify", "2FA Verify"
    TWO_FA_ENABLE = "two_fa_enable", "2FA Enable"
    TWO_FA_DISABLE = "two_fa_disable", "2FA Disable"
    PERMISSION_DENIED = "permission_denied", "Permission Denied"
    DEVICE_REVOKE = "device_revoke", "Device Revoke"
    RATE_LIMITED = "rate_limited", "Rate Limited"


class AuditOutcome(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"
    BLOCKED = "blocked", "Blocked"
