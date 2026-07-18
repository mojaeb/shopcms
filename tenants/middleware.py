"""Tenant middleware - resolve store from domain."""

import logging

from django.conf import settings
from django.http import Http404, HttpResponseRedirect

from tenants.context import clear_current_store
from tenants.repositories.store import DomainRepository
from tenants.services.store import StoreInactiveError, StoreNotFoundError, StoreService

logger = logging.getLogger(__name__)

# Paths that don't require tenant resolution
EXEMPT_PREFIXES = (
    "/admin/",
    "/api/v1/health/",
    "/api/v1/super-admin/",
    "/static/",
    "/media/",
    "/__debug__/",
)


class TenantMiddleware:
    """Resolve current store from request host and attach to request."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.store_service = StoreService()
        self.domain_repo = DomainRepository()

    def __call__(self, request):
        if self._is_exempt(request.path):
            return self.get_response(request)

        clear_current_store()

        try:
            host = request.get_host()
            store = self.store_service.resolve_by_host(host)

            # Redirect to primary domain if configured
            redirect_url = self._check_primary_redirect(request, store, host)
            if redirect_url:
                return HttpResponseRedirect(redirect_url)

            self.store_service.activate(store)
            request.store = store
            request.theme_slug = store.effective_theme_slug

        except StoreNotFoundError:
            if settings.DEBUG:
                request.store = None
                request.theme_slug = "default"
            else:
                raise Http404("فروشگاه یافت نشد")
        except StoreInactiveError:
            raise Http404("فروشگاه غیرفعال است")

        response = self.get_response(request)
        clear_current_store()
        return response

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in EXEMPT_PREFIXES)

    def _check_primary_redirect(self, request, store, host: str) -> str | None:
        if not request.method == "GET":
            return None

        current_domain = self.domain_repo.model.objects.filter(
            domain=host.lower(),
            store=store,
            is_active=True,
        ).first()

        if not current_domain or not current_domain.redirect_to_primary:
            return None

        primary = self.domain_repo.get_primary_for_store(store)
        if not primary or primary.domain == host.lower():
            return None

        scheme = "https" if current_domain.ssl_enabled else request.scheme
        return f"{scheme}://{primary.domain}{request.get_full_path()}"
