"""Store context processor for templates."""

from accounts.services.permissions import PermissionService
from tenants.context import get_current_store
from tenants.services.theme_settings import ThemeSettingsService
from tenants.theme.engine import ThemeEngine


def store_context(request):
    store = get_current_store() or getattr(request, "store", None)
    user = getattr(request, "user", None)
    google_site_verification = ""
    if store:
        from tenants.services.seo import SeoService

        google_site_verification = SeoService().get_verification_token(store)
    return {
        "store": store,
        "theme_slug": getattr(request, "theme_slug", "default"),
        "is_store_staff": PermissionService().is_store_staff(user, store),
        "google_site_verification": google_site_verification,
    }


def theme_context(request):
    store = get_current_store() or getattr(request, "store", None)
    engine = ThemeEngine()
    theme_settings = ThemeSettingsService().get_theme_settings(store)
    return {
        "theme_slug": engine.get_theme_slug(store),
        "theme_engine": engine,
        "theme_settings": theme_settings,
    }
