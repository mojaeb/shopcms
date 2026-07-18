"""Theme resolution service."""

import logging
from pathlib import Path

from django.conf import settings
from django.template.loader import get_template

from tenants.context import get_current_store

logger = logging.getLogger(__name__)


class ThemeResolver:
    """
    Resolve template paths with fallback:
    themes/{current_theme}/page.html -> themes/default/page.html
    """

    def __init__(self, themes_dir: Path | None = None):
        self.themes_dir = themes_dir or (settings.BASE_DIR / "themes")

    def get_theme_slug(self, store=None) -> str:
        store = store or get_current_store()
        if store:
            return store.effective_theme_slug
        return "default"

    def resolve_template_name(self, template_name: str, store=None) -> str:
        """
        Return the best matching template path.
        template_name: e.g. 'home.html' or 'product.html'
        """
        theme_slug = self.get_theme_slug(store)
        themed = f"themes/{theme_slug}/{template_name}"
        default = f"themes/default/{template_name}"

        if self._template_exists(themed):
            return themed
        if self._template_exists(default):
            return default
        return themed  # let Django raise TemplateDoesNotExist

    def _template_exists(self, template_name: str) -> bool:
        path = settings.BASE_DIR / template_name
        return path.exists()

    def get_template(self, template_name: str, store=None):
        resolved = self.resolve_template_name(template_name, store)
        return get_template(resolved)

    def list_available_templates(self, theme_slug: str) -> list[str]:
        theme_path = self.themes_dir / theme_slug
        if not theme_path.exists():
            return []
        files = []
        for f in theme_path.rglob("*.html"):
            rel = f.relative_to(theme_path)
            files.append(str(rel).replace("\\", "/"))
        return sorted(files)
