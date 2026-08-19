"""Store admin shipping API."""

from decimal import Decimal

from django.db import transaction
from ninja import Router, Schema
from ninja.errors import HttpError

from dashboard.authentication_store import store_settings_auth
from shipping.data.province_adjacency import ADJACENT_PROVINCES
from shipping.enums import CalculationMode, ShippingProviderType, ShippingZoneTier
from shipping.models import ShippingMethod, ShippingPrice, ShippingZone
from tenants.context import get_current_store

router = Router(auth=store_settings_auth)

# استان‌های ایران بر اساس داده‌ی موجود در province_adjacency
_IRAN_PROVINCES: list[str] = sorted(ADJACENT_PROVINCES.keys())


class ZoneSchema(Schema):
    name: str
    provinces: list[str] = []
    cities: list[str] = []
    is_active: bool = True


class MethodCreateSchema(Schema):
    """Create a shipping method.

    `config` is a free-form dict. Known keys:
    - all providers: `fixed_price`, `origin_city`, `extra_cost_flat`, `extra_cost_percent`
    - provider=peyk: `delivery_cities` (list of city names; empty = all cities)
    - provider=post: `max_weight_kg`
    """

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
    payment_type: str = "prepaid"


class PriceCreateSchema(Schema):
    from_city: str = ""
    to_city: str = ""
    zone_tier: str = ""
    weight_min_kg: float = 0
    weight_max_kg: float | None = None
    price: float
    extra_per_kg: float = 0


class BulkPriceRowSchema(Schema):
    from_city: str = ""
    to_city: str = ""
    zone_tier: str = ""
    weight_min_kg: float = 0
    weight_max_kg: float | None = None
    price: float
    extra_per_kg: float = 0


class BulkPriceImportSchema(Schema):
    rows: list[BulkPriceRowSchema]
    replace_all: bool = False  # اگر True کل جدول فعلی را حذف و جایگزین کن


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
            "payment_type": m.payment_type,
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
        payment_type=payload.payment_type,
    )
    return {"id": method.id, "slug": method.slug}


@router.post("/methods/{method_id}/prices")
def add_price(request, method_id: int, payload: PriceCreateSchema):
    store = _store(request)
    method = ShippingMethod.objects.get(pk=method_id, store=store)
    price = ShippingPrice.objects.create(method=method, **payload.dict())
    return {"id": price.id, "price": str(price.price)}


@router.post("/methods/{method_id}/prices/bulk")
def bulk_import_prices(request, method_id: int, payload: BulkPriceImportSchema):
    """Bulk upsert shipping price rows.

    کلید طبیعی برای upsert: (from_city, to_city, zone_tier, weight_min_kg).
    اگر ردیفی با همین کلید وجود داشت، price/weight_max_kg/extra_per_kg آن update می‌شود.
    overlap بین ردیف‌های هم‌مقصد تشخیص داده و در warnings برگردانده می‌شود (رد نمی‌شود).
    """
    store = _store(request)
    try:
        method = ShippingMethod.objects.get(pk=method_id, store=store)
    except ShippingMethod.DoesNotExist:
        raise HttpError(404, "روش ارسال یافت نشد")

    errors: list[str] = []
    for idx, row in enumerate(payload.rows, start=1):
        wmin = Decimal(str(row.weight_min_kg))
        wmax = Decimal(str(row.weight_max_kg)) if row.weight_max_kg is not None else None
        if wmax is not None and wmin >= wmax:
            errors.append(f"ردیف {idx}: وزن حداقل باید کمتر از وزن حداکثر باشد")

    if errors:
        raise HttpError(400, " | ".join(errors))

    warnings: list[str] = []
    warnings.extend(_detect_overlaps(payload.rows))

    with transaction.atomic():
        if payload.replace_all:
            ShippingPrice.objects.filter(method=method).delete()

        created_count = 0
        updated_count = 0

        for row in payload.rows:
            wmin = Decimal(str(row.weight_min_kg))
            wmax = Decimal(str(row.weight_max_kg)) if row.weight_max_kg is not None else None

            obj, created = ShippingPrice.objects.update_or_create(
                method=method,
                from_city=row.from_city,
                to_city=row.to_city,
                zone_tier=row.zone_tier,
                weight_min_kg=wmin,
                defaults={
                    "weight_max_kg": wmax,
                    "price": Decimal(str(row.price)),
                    "extra_per_kg": Decimal(str(row.extra_per_kg)),
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

    return {
        "created": created_count,
        "updated": updated_count,
        "warnings": warnings,
    }


@router.get("/methods/{method_id}/prices/export")
def export_prices(request, method_id: int):
    """Export all price rows of a method as JSON (ready for re-upload via bulk import)."""
    store = _store(request)
    try:
        method = ShippingMethod.objects.get(pk=method_id, store=store)
    except ShippingMethod.DoesNotExist:
        raise HttpError(404, "روش ارسال یافت نشد")

    rows = [
        {
            "from_city": p.from_city,
            "to_city": p.to_city,
            "zone_tier": p.zone_tier,
            "weight_min_kg": float(p.weight_min_kg),
            "weight_max_kg": float(p.weight_max_kg) if p.weight_max_kg is not None else None,
            "price": float(p.price),
            "extra_per_kg": float(p.extra_per_kg),
        }
        for p in ShippingPrice.objects.filter(method=method).order_by("from_city", "to_city", "weight_min_kg")
    ]
    return {
        "method_id": method.id,
        "method_name": method.name,
        "rows": rows,
        "total": len(rows),
    }


@router.get("/locations")
def list_locations(request):
    """لیست استان‌های ایران برای فرم‌های ادمین (select به‌جای تایپ آزاد)."""
    _store(request)
    return {
        "provinces": _IRAN_PROVINCES,
        "zone_tiers": [{"value": t.value, "label": t.label} for t in ShippingZoneTier],
    }


def _detect_overlaps(rows: list[BulkPriceRowSchema]) -> list[str]:
    """هشدار overlap بین ردیف‌های هم‌مقصد با بازه‌ی وزنی متقاطع."""
    warnings: list[str] = []
    # گروه‌بندی بر اساس (from_city, to_city, zone_tier)
    groups: dict[tuple, list] = {}
    for r in rows:
        key = (r.from_city, r.to_city, r.zone_tier)
        groups.setdefault(key, []).append(r)

    for key, group in groups.items():
        if len(group) < 2:
            continue
        sorted_g = sorted(group, key=lambda r: r.weight_min_kg)
        for i in range(len(sorted_g) - 1):
            a = sorted_g[i]
            b = sorted_g[i + 1]
            a_max = a.weight_max_kg
            b_min = b.weight_min_kg
            if a_max is not None and b_min < a_max:
                dest = f"from={key[0] or '*'} to={key[1] or '*'} tier={key[2] or '*'}"
                warnings.append(
                    f"overlap در {dest}: ردیف وزن {a.weight_min_kg}–{a_max} با {b_min}–{b.weight_max_kg} هم‌پوشانی دارد"
                )
    return warnings


@router.get("/providers")
def list_provider_types(request):
    return {
        "providers": [{"value": c.value, "label": c.label} for c in ShippingProviderType],
        "calculation_modes": [{"value": c.value, "label": c.label} for c in CalculationMode],
    }
