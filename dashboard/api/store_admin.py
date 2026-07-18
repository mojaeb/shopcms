"""Store Admin API endpoints."""

from ninja import Body, Router
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination, paginate

from dashboard.api.store_admin_schemas import (
    DashboardStatsSchema,
    GeneralSettingsUpdateSchema,
    MemberSchema,
    ModuleStubSchema,
    SettingsOverviewSchema,
    TaxSettingsSchema,
    TaxSettingsUpdateSchema,
    TeamMemberCreateSchema,
    UserRoleUpdateSchema,
    UserStatusUpdateSchema,
)
from dashboard.authentication_store import (
    require_store_admin,
    store_admin_auth,
    store_content_auth,
    store_settings_auth,
)
from dashboard.services.store_admin import StoreAdminService
from tenants.context import get_current_store

router = Router()
service = StoreAdminService()


def _get_store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


def _member_schema(m) -> MemberSchema:
    return MemberSchema(
        id=m.id,
        user_id=m.user_id,
        phone=m.user.phone,
        full_name=m.user.full_name,
        role=m.role.codename,
        status=m.status,
        is_primary=m.is_primary,
        created_at=m.created_at.isoformat(),
    )


@router.get("/dashboard", response=DashboardStatsSchema, auth=store_admin_auth)
def dashboard_stats(request):
    return service.get_dashboard_stats(_get_store(request))


@router.get("/settings", response=SettingsOverviewSchema, auth=store_settings_auth)
def settings_overview(request):
    overview = service.get_settings_overview(_get_store(request))
    return overview


@router.put("/settings/general", auth=store_settings_auth)
def update_general_settings(request, payload: GeneralSettingsUpdateSchema):
    data = {k: v for k, v in payload.dict().items() if v is not None}
    result = service.update_general_settings(_get_store(request), data)
    return result


@router.put("/settings/tax", response=TaxSettingsSchema, auth=store_settings_auth)
def update_tax_settings(request, payload: TaxSettingsUpdateSchema):
    data = {k: v for k, v in payload.dict().items() if v is not None}
    return service.update_tax_settings(_get_store(request), data)


@router.put("/settings/payment", auth=store_settings_auth)
def update_payment_settings(request, payload: dict):
    return service.update_group_settings(_get_store(request), "payment", payload)


@router.put("/settings/shipping", auth=store_settings_auth)
def update_shipping_settings(request, payload: dict):
    return service.update_group_settings(_get_store(request), "shipping", payload)


@router.put("/settings/theme", auth=store_settings_auth)
def update_theme_settings(request, payload: dict = Body(...)):
    return service.update_theme_settings(_get_store(request), payload or {})


@router.get("/users", response=list[MemberSchema], auth=store_admin_auth)
@paginate(PageNumberPagination, page_size=20)
def list_customers(request, search: str = "", role: str | None = None):
    store = _get_store(request)
    return [_member_schema(m) for m in service.list_users(store, search, role or "customer")]


@router.get("/users/{user_id}", response=MemberSchema, auth=store_admin_auth)
def get_customer(request, user_id: int):
    try:
        return _member_schema(service.get_user_membership(_get_store(request), user_id))
    except Exception:
        raise HttpError(404, "کاربر یافت نشد")


@router.put("/users/{user_id}/status", response=MemberSchema, auth=store_admin_auth)
@require_store_admin
def update_user_status(request, user_id: int, payload: UserStatusUpdateSchema):
    try:
        return _member_schema(
            service.update_user_status(_get_store(request), user_id, payload.status)
        )
    except Exception:
        raise HttpError(404, "کاربر یافت نشد")


@router.put("/users/{user_id}/role", response=MemberSchema, auth=store_admin_auth)
@require_store_admin
def update_user_role(request, user_id: int, payload: UserRoleUpdateSchema):
    try:
        return _member_schema(
            service.update_user_role(_get_store(request), user_id, payload.role)
        )
    except Role.DoesNotExist:
        raise HttpError(400, "نقش نامعتبر است")
    except Exception:
        raise HttpError(404, "کاربر یافت نشد")


@router.get("/team", response=list[MemberSchema], auth=store_admin_auth)
def list_team(request):
    store = _get_store(request)
    return [_member_schema(m) for m in service.list_team(store)]


@router.post("/team", response=MemberSchema, auth=store_admin_auth)
@require_store_admin
def add_team_member(request, payload: TeamMemberCreateSchema):
    try:
        membership = service.add_team_member(
            _get_store(request),
            payload.phone,
            payload.role,
            payload.first_name,
            payload.last_name,
        )
        return _member_schema(membership)
    except Exception as e:
        raise HttpError(400, str(e))


from accounts.models import Role  # noqa: E402
