"""Test settings - fast, isolated, CI-friendly."""

from .base import *  # noqa: F401, F403

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"
ALLOWED_HOSTS = ["*"]

OTP_USE_FIXED_CODE = True
OTP_FIXED_CODE = "12345"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "shopcms-test",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

RATE_LIMIT_ENABLED = False

NINJA_DEFAULT_THROTTLE_RATES = {
    "anon": "10000/min",
    "auth": "10000/min",
    "otp_send": "10000/min",
    "auth_refresh": "10000/min",
}

LOGGING["root"]["level"] = "WARNING"  # noqa: F405
