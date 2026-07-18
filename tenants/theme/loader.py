"""Django template loader with theme fallback chain."""

import logging
from pathlib import Path

from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader

from tenants.context import get_current_store
from tenants.services.theme import ThemeResolver

logger = logging.getLogger(__name__)

SKIP_PREFIXES = (
    "admin/",
    "django/",
    "registration/",
    "debug_toolbar/",
    "store_admin/",
)


class ThemeLoader(BaseLoader):
    """
    Resolve templates with theme fallback:
    themes/{current}/page.html -> themes/default/page.html
    """

    def __init__(self, engine, themes_dir=None):
        super().__init__(engine)
        self.themes_dir = Path(themes_dir or settings.BASE_DIR / "themes")

    def get_template_sources(self, template_name):
        if template_name.startswith(SKIP_PREFIXES):
            return

        if template_name.startswith("themes/"):
            yield from self._yield_resolved(template_name, template_name)
            return

        resolver = ThemeResolver(themes_dir=self.themes_dir)
        store = get_current_store()
        resolved = resolver.resolve_template_name(template_name, store)
        yield from self._yield_resolved(resolved, template_name)

    def _yield_resolved(self, resolved_path: str, template_name: str):
        full_path = settings.BASE_DIR / resolved_path
        if full_path.exists():
            yield Origin(
                name=str(full_path),
                template_name=template_name,
                loader=self,
            )

    def get_contents(self, origin):
        try:
            with open(origin.name, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise TemplateDoesNotExist(origin) from e
