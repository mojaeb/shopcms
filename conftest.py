"""Shared pytest fixtures."""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_django_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def security_test_settings(settings):
    settings.RATE_LIMIT_ENABLED = False
    settings.NINJA_DEFAULT_THROTTLE_RATES = {
        "anon": "10000/min",
        "auth": "10000/min",
        "otp_send": "10000/min",
        "auth_refresh": "10000/min",
    }
