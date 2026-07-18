"""Store API endpoints."""

from ninja import Router, Schema

from tenants.context import get_current_store
from tenants.theme.engine import ThemeEngine

router = Router()


class StoreInfoSchema(Schema):
    id: int
    name: str
    slug: str
    store_type: str
    status: str
    theme_slug: str
    currency: str
    timezone: str
    language: str
    tax_enabled: bool
    tax_percent: str


@router.get("/current", response=StoreInfoSchema)
def current_store(request):
    """Get current store based on request domain."""
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    return StoreInfoSchema(
        id=store.id,
        name=store.name,
        slug=store.slug,
        store_type=store.store_type,
        status=store.status,
        theme_slug=store.effective_theme_slug,
        currency=store.currency,
        timezone=store.timezone,
        language=store.language,
        tax_enabled=store.tax_enabled,
        tax_percent=str(store.tax_percent),
    )


@router.get("/theme/info")
def theme_info(request):
    """Full theme engine info for current store."""
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    return ThemeEngine().get_theme_info(store)


@router.get("/theme/templates")
def theme_templates(request):
    """List available templates for current store theme."""
    store = get_current_store() or getattr(request, "store", None)
    engine = ThemeEngine()
    return engine.get_theme_info(store)
