"""Store admin shipping API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from dashboard.authentication_store import store_settings_auth
from shipping.enums import CalculationMode, ShippingProviderType
from shipping.models import ShippingMethod, ShippingPrice, ShippingZone
from tenants.context import get_current_store

router = Router(auth=store_settings_auth)


class ZoneSchema(Schema):
    name: str
    provinces: list[str] = []
    cities: list[str] = []
    is_active: bool = True


class MethodCreateSchema(Schema):
    name: str
    slug: str
    provider: str
    calculation_mode: str
    config: dict = {}
    zone_id: int | None = None
    is_active: bool = True
    sort_order: int = 0
    min_order_amount: float = 0
    free_shipping_threshold: float | None = None
    estimated_days: int = 3


class PriceCreateSchema(Schema):
    from_city: str = ""
    to_city: str = ""
    weight_min_kg: float = 0
    weight_max_kg: float | None = None
    price: float
    extra_per_kg: float = 0


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/zones")
def list_zones(request):
    store = _store(request)
    return [
        {"id": z.id, "name": z.name, "provinces": z.provinces, "cities": z.cities, "is_active": z.is_active}
        for z in ShippingZone.objects.filter(store=store)
    ]


@router.post("/zones")
def create_zone(request, payload: ZoneSchema):
    store = _store(request)
    zone = ShippingZone.objects.create(store=store, **payload.dict())
    return {"id": zone.id, "name": zone.name}


@router.get("/methods")
def list_methods(request):
    store = _store(request)
    methods = ShippingMethod.objects.filter(store=store).order_by("sort_order")
    return [
        {
            "id": m.id,
            "name": m.name,
            "slug": m.slug,
            "provider": m.provider,
            "calculation_mode": m.calculation_mode,
            "is_active": m.is_active,
            "config": m.config,
            "zone_id": m.zone_id,
            "estimated_days": m.estimated_days,
        }
        for m in methods
    ]


@router.post("/methods")
def create_method(request, payload: MethodCreateSchema):
    store = _store(request)
    zone = None
    if payload.zone_id:
        zone = ShippingZone.objects.get(pk=payload.zone_id, store=store)
    method = ShippingMethod.objects.create(
        store=store,
        zone=zone,
        name=payload.name,
        slug=payload.slug,
        provider=payload.provider,
        calculation_mode=payload.calculation_mode,
        config=payload.config,
        is_active=payload.is_active,
        sort_order=payload.sort_order,
        min_order_amount=payload.min_order_amount,
        free_shipping_threshold=payload.free_shipping_threshold,
        estimated_days=payload.estimated_days,
    )
    return {"id": method.id, "slug": method.slug}


@router.post("/methods/{method_id}/prices")
def add_price(request, method_id: int, payload: PriceCreateSchema):
    store = _store(request)
    method = ShippingMethod.objects.get(pk=method_id, store=store)
    price = ShippingPrice.objects.create(method=method, **payload.dict())
    return {"id": price.id, "price": str(price.price)}


@router.get("/providers")
def list_provider_types(request):
    return {
        "providers": [{"value": c.value, "label": c.label} for c in ShippingProviderType],
        "calculation_modes": [{"value": c.value, "label": c.label} for c in CalculationMode],
    }
