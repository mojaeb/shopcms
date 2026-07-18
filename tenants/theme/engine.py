"""Theme rendering engine."""

import logging
from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from tenants.context import get_current_store
from tenants.services.theme import ThemeResolver
from tenants.theme.pages import STOREFRONT_PAGES

logger = logging.getLogger(__name__)


class ThemeEngine:
    """Central theme rendering with fallback and context injection."""

    def __init__(self):
        self.resolver = ThemeResolver()

    def get_theme_slug(self, store=None) -> str:
        return self.resolver.get_theme_slug(store)

    def resolve(self, template_name: str, store=None) -> str:
        return self.resolver.resolve_template_name(template_name, store)

    def build_context(self, request: HttpRequest, extra: dict | None = None) -> dict:
        store = get_current_store() or getattr(request, "store", None)
        context = {
            "store": store,
            "theme_slug": self.get_theme_slug(store),
            "theme_pages": list(STOREFRONT_PAGES.keys()),
        }
        if extra:
            context.update(extra)
        return context

    def render(
        self,
        request: HttpRequest,
        template_name: str,
        context: dict | None = None,
        status: int = 200,
    ) -> HttpResponse:
        store = get_current_store() or getattr(request, "store", None)
        resolved = self.resolve(template_name, store)
        full_context = self.build_context(request, context)
        return render(request, resolved, full_context, status=status)

    def render_page(
        self,
        request: HttpRequest,
        page_key: str,
        context: dict | None = None,
        status: int = 200,
    ) -> HttpResponse:
        if page_key not in STOREFRONT_PAGES:
            raise ValueError(f"Unknown page: {page_key}")
        return self.render(request, STOREFRONT_PAGES[page_key], context, status)

    def get_theme_info(self, store=None) -> dict:
        theme_slug = self.get_theme_slug(store)
        available = self.resolver.list_available_templates(theme_slug)
        default_templates = self.resolver.list_available_templates("default")
        overridden = [t for t in available if t in default_templates]
        inherited = [t for t in default_templates if t not in available]

        return {
            "theme_slug": theme_slug,
            "templates": available,
            "default_templates": default_templates,
            "overridden": overridden,
            "inherited": inherited,
            "pages": STOREFRONT_PAGES,
        }

    def include_path(self, partial: str, store=None) -> str:
        """Resolve partial path for {% theme_include %} tag."""
        name = partial if partial.endswith(".html") else f"{partial}.html"
        if not name.startswith("partials/"):
            name = f"partials/{name}"
        return self.resolve(name, store)
