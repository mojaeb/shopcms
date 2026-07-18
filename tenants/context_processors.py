"""Store context processor for templates."""

from accounts.services.permissions import PermissionService
from tenants.context import get_current_store
from tenants.services.theme_settings import ThemeSettingsService
from tenants.theme.engine import ThemeEngine


def store_context(request):
    store = get_current_store() or getattr(request, "store", None)
    user = getattr(request, "user", None)
    return {
        "store": store,
        "theme_slug": getattr(request, "theme_slug", "default"),
        "is_store_staff": PermissionService().is_store_staff(user, store),
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
