"""Super Admin API endpoints."""

from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination, paginate

from dashboard.api.schemas import (
    DashboardStatsSchema,
    DomainCreateSchema,
    DomainSchema,
    DomainUpdateSchema,
    PaymentSettingsSchema,
    PluginSchema,
    ShippingSettingsSchema,
    StoreAdminCreateSchema,
    StoreAdminSchema,
    StoreCreateSchema,
    StoreDetailSchema,
    StoreListSchema,
    StorePluginSchema,
    StorePluginUpdateSchema,
    StoreUpdateSchema,
    TaxSettingsSchema,
    TaxSettingsUpdateSchema,
    ThemeSchema,
)
from dashboard.authentication import super_admin_auth
from dashboard.services.super_admin import StoreNotFoundError, SuperAdminError, SuperAdminService

router = Router(auth=super_admin_auth)
service = SuperAdminService()


def _store_list(store) -> StoreListSchema:
    return StoreListSchema(
        id=store.id,
        name=store.name,
        slug=store.slug,
        store_type=store.store_type,
        status=store.status,
        currency=store.currency,
        theme_slug=store.effective_theme_slug,
        domain_count=getattr(store, "domain_count", store.domains.count()),
        member_count=getattr(store, "member_count", 0),
        tax_enabled=store.tax_enabled,
        created_at=store.created_at.isoformat(),
    )


def _store_detail(store) -> StoreDetailSchema:
    return StoreDetailSchema(
        id=store.id,
        name=store.name,
        slug=store.slug,
        store_type=store.store_type,
        status=store.status,
        currency=store.currency,
        theme_slug=store.effective_theme_slug,
        domain_count=getattr(store, "domain_count", store.domains.count()),
        member_count=getattr(store, "member_count", 0),
        tax_enabled=store.tax_enabled,
        created_at=store.created_at.isoformat(),
        timezone=store.timezone,
        language=store.language,
        tax_percent=str(store.tax_percent),
        theme_id=store.theme_id,
        default_theme_id=store.default_theme_id,
    )


@router.get("/stats", response=DashboardStatsSchema)
def dashboard_stats(request):
    return service.get_dashboard_stats()


@router.get("/themes", response=list[ThemeSchema])
def list_themes(request):
    return [
        ThemeSchema(
            id=t.id,
            name=t.name,
            slug=t.slug,
            directory=t.directory,
            is_default=t.is_default,
        )
        for t in service.list_themes()
    ]


@router.get("/plugins", response=list[PluginSchema])
def list_plugins(request, store_type: str | None = None):
    return [
        PluginSchema(
            id=p.id,
            codename=p.codename,
            name=p.name,
            description=p.description,
            compatible_store_types=p.compatible_store_types,
        )
        for p in service.list_plugins(store_type)
    ]


@router.get("/stores", response=list[StoreListSchema])
@paginate(PageNumberPagination, page_size=20)
def list_stores(request, search: str = "", status: str | None = None):
    return [_store_list(s) for s in service.list_stores(search, status)]


@router.post("/stores", response=StoreDetailSchema)
def create_store(request, payload: StoreCreateSchema):
    try:
        store = service.create_store(payload.dict())
        return _store_detail(store)
    except Exception as e:
        raise HttpError(400, str(e))


@router.get("/stores/{store_id}", response=StoreDetailSchema)
def get_store(request, store_id: int):
    try:
        return _store_detail(service.get_store(store_id))
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.put("/stores/{store_id}", response=StoreDetailSchema)
def update_store(request, store_id: int, payload: StoreUpdateSchema):
    try:
        data = {k: v for k, v in payload.dict().items() if v is not None}
        store = service.update_store(store_id, data)
        return _store_detail(store)
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.delete("/stores/{store_id}")
def delete_store(request, store_id: int, hard: bool = False):
    try:
        service.delete_store(store_id, hard=hard)
        return {"detail": "فروشگاه حذف شد"}
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.get("/stores/{store_id}/domains", response=list[DomainSchema])
def list_domains(request, store_id: int):
    try:
        return [
            DomainSchema(
                id=d.id,
                domain=d.domain,
                is_primary=d.is_primary,
                ssl_enabled=d.ssl_enabled,
                redirect_to_primary=d.redirect_to_primary,
                is_active=d.is_active,
            )
            for d in service.list_domains(store_id)
        ]
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.post("/stores/{store_id}/domains", response=DomainSchema)
def add_domain(request, store_id: int, payload: DomainCreateSchema):
    try:
        domain = service.add_domain(store_id, payload.dict())
        return DomainSchema(
            id=domain.id,
            domain=domain.domain,
            is_primary=domain.is_primary,
            ssl_enabled=domain.ssl_enabled,
            redirect_to_primary=domain.redirect_to_primary,
            is_active=domain.is_active,
        )
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")
    except Exception as e:
        raise HttpError(400, str(e))


@router.put("/stores/{store_id}/domains/{domain_id}", response=DomainSchema)
def update_domain(request, store_id: int, domain_id: int, payload: DomainUpdateSchema):
    try:
        data = {k: v for k, v in payload.dict().items() if v is not None}
        domain = service.update_domain(store_id, domain_id, data)
        return DomainSchema(
            id=domain.id,
            domain=domain.domain,
            is_primary=domain.is_primary,
            ssl_enabled=domain.ssl_enabled,
            redirect_to_primary=domain.redirect_to_primary,
            is_active=domain.is_active,
        )
    except Domain.DoesNotExist:
        raise HttpError(404, "دامنه یافت نشد")


@router.delete("/stores/{store_id}/domains/{domain_id}")
def delete_domain(request, store_id: int, domain_id: int):
    try:
        service.delete_domain(store_id, domain_id)
        return {"detail": "دامنه حذف شد"}
    except Domain.DoesNotExist:
        raise HttpError(404, "دامنه یافت نشد")


@router.get("/stores/{store_id}/admins", response=list[StoreAdminSchema])
def list_admins(request, store_id: int):
    try:
        return [
            StoreAdminSchema(
                id=m.user.id,
                phone=m.user.phone,
                full_name=m.user.full_name,
                is_primary=m.is_primary,
                created_at=m.created_at.isoformat(),
            )
            for m in service.list_store_admins(store_id)
        ]
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.post("/stores/{store_id}/admins", response=StoreAdminSchema)
def create_admin(request, store_id: int, payload: StoreAdminCreateSchema):
    try:
        result = service.create_store_admin(store_id, payload.dict())
        user = result["user"]
        membership = result["membership"]
        return StoreAdminSchema(
            id=user.id,
            phone=user.phone,
            full_name=user.full_name,
            is_primary=membership.is_primary,
            created_at=membership.created_at.isoformat(),
        )
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")
    except Exception as e:
        raise HttpError(400, str(e))


@router.get("/stores/{store_id}/plugins", response=list[StorePluginSchema])
def list_store_plugins(request, store_id: int):
    try:
        items = service.list_store_plugins(store_id)
        return [
            StorePluginSchema(
                plugin=PluginSchema(
                    id=item["plugin"].id,
                    codename=item["plugin"].codename,
                    name=item["plugin"].name,
                    description=item["plugin"].description,
                    compatible_store_types=item["plugin"].compatible_store_types,
                ),
                is_enabled=item["is_enabled"],
                settings=item["settings"],
                store_plugin_id=item["store_plugin_id"],
            )
            for item in items
        ]
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.put("/stores/{store_id}/plugins/{plugin_id}", response=StorePluginSchema)
def update_store_plugin(request, store_id: int, plugin_id: int, payload: StorePluginUpdateSchema):
    try:
        sp = service.set_store_plugin(store_id, plugin_id, payload.is_enabled, payload.settings)
        plugin = sp.plugin
        return StorePluginSchema(
            plugin=PluginSchema(
                id=plugin.id,
                codename=plugin.codename,
                name=plugin.name,
                description=plugin.description,
                compatible_store_types=plugin.compatible_store_types,
            ),
            is_enabled=sp.is_enabled,
            settings=sp.settings,
            store_plugin_id=sp.id,
        )
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")
    except SuperAdminError as e:
        raise HttpError(400, str(e))


@router.get("/stores/{store_id}/settings/tax", response=TaxSettingsSchema)
def get_tax_settings(request, store_id: int):
    try:
        return service.get_tax_settings(store_id)
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.put("/stores/{store_id}/settings/tax", response=TaxSettingsSchema)
def update_tax_settings(request, store_id: int, payload: TaxSettingsUpdateSchema):
    try:
        data = {k: v for k, v in payload.dict().items() if v is not None}
        return service.update_tax_settings(store_id, data)
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.get("/stores/{store_id}/settings/payment", response=PaymentSettingsSchema)
def get_payment_settings(request, store_id: int):
    try:
        return service.get_payment_settings(store_id)
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.put("/stores/{store_id}/settings/payment", response=PaymentSettingsSchema)
def update_payment_settings(request, store_id: int, payload: PaymentSettingsSchema):
    try:
        return service.update_payment_settings(store_id, payload.dict())
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.get("/stores/{store_id}/settings/shipping", response=ShippingSettingsSchema)
def get_shipping_settings(request, store_id: int):
    try:
        return service.get_shipping_settings(store_id)
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


@router.put("/stores/{store_id}/settings/shipping", response=ShippingSettingsSchema)
def update_shipping_settings(request, store_id: int, payload: ShippingSettingsSchema):
    try:
        return service.update_shipping_settings(store_id, payload.dict())
    except StoreNotFoundError:
        raise HttpError(404, "فروشگاه یافت نشد")


from tenants.models import Domain  # noqa: E402
