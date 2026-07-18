"""Global API rate limiting middleware."""

import json

from django.conf import settings
from django.http import JsonResponse

from core.services.audit import AuditService
from core.services.rate_limit import RateLimitExceeded, RateLimitService
from core.utils.request import get_client_ip


class APIRateLimitMiddleware:
    """Apply coarse IP-based limits to API routes."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limiter = RateLimitService()
        self.audit = AuditService()

    def __call__(self, request):
        if self._should_limit(request):
            ip = get_client_ip(request) or "unknown"
            limit = getattr(settings, "RATE_LIMIT_API_ANON", 120)
            window = getattr(settings, "RATE_LIMIT_API_WINDOW", 60)
            try:
                self.rate_limiter.hit("api_ip", ip, limit=limit, window_seconds=window)
            except RateLimitExceeded as exc:
                self.audit.log_rate_limited(request, "api_ip", ip)
                return JsonResponse(
                    {"detail": str(exc)},
                    status=429,
                    headers={"Retry-After": str(exc.retry_after or window)},
                )
        return self.get_response(request)

    def _should_limit(self, request) -> bool:
        if not getattr(settings, "RATE_LIMIT_ENABLED", True):
            return False
        path = request.path
        if not path.startswith("/api/v1/"):
            return False
        exempt = (
            "/api/v1/health/",
        )
        return not any(path.startswith(prefix) for prefix in exempt)
