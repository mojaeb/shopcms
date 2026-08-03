"""Staging / test-server settings (HTTP-friendly, production-like)."""

from .base import *  # noqa: F401, F403

DEBUG = env.bool("DEBUG", default=False)  # noqa: F405

# Test servers often run plain HTTP behind a simple reverse proxy
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)  # noqa: F405
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)  # noqa: F405
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)  # noqa: F405
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

OTP_USE_FIXED_CODE = env.bool("OTP_USE_FIXED_CODE", default=True)  # noqa: F405
