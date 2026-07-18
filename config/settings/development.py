"""Development settings."""

from .base import *  # noqa: F401, F403

DEBUG = True
OTP_USE_FIXED_CODE = True
# Allow several OTP sends while testing register → login locally
OTP_RATE_LIMIT_COUNT = 10
OTP_RATE_LIMIT_SECONDS = 60

NINJA_DEFAULT_THROTTLE_RATES = {
    "anon": "240/min",
    "auth": "120/min",
    "otp_send": "30/min",
    "auth_refresh": "60/min",
}

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "shop1.local", ".local"]

# Use console email backend in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Debug toolbar (optional, enabled when installed)
try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F811
    MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F811
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass

# Relaxed cache for development without Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "shopcms-dev",
    }
}
