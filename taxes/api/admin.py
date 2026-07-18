"""Store admin tax rules API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from dashboard.authentication_store import store_settings_auth
from taxes.enums import TaxRuleScope
from taxes.services.tax import TaxError, TaxService
from tenants.context import get_current_store

router = Router(auth=store_settings_auth)
service = TaxService()


class TaxRuleCreateSchema(Schema):
    name: str
    rate_percent: float
    scope: str = TaxRuleScope.ALL
    category_id: int | None = None
    product_id: int | None = None
    is_active: bool = True
    priority: int = 0


class TaxRuleUpdateSchema(Schema):
    name: str | None = None
    rate_percent: float | None = None
    scope: str | None = None
    category_id: int | None = None
    product_id: int | None = None
    is_active: bool | None = None
    priority: int | None = None


class TaxSettingsUpdateSchema(Schema):
    tax_enabled: bool | None = None
    tax_percent: float | None = None
    tax_on_shipping: bool | None = None


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/settings")
def get_settings(request):
    return service.get_tax_settings(_store(request))


@router.put("/settings")
def update_settings(request, payload: TaxSettingsUpdateSchema):
    data = {k: v for k, v in payload.dict().items() if v is not None}
    return service.update_tax_settings(_store(request), data)


@router.get("/rules")
def list_rules(request):
    store = _store(request)
    return [service.serialize_rule(r) for r in service.list_rules(store)]


@router.post("/rules")
def create_rule(request, payload: TaxRuleCreateSchema):
    store = _store(request)
    try:
        rule = service.create_rule(store, payload.dict())
        return service.serialize_rule(rule)
    except TaxError as e:
        raise HttpError(400, str(e))


@router.put("/rules/{rule_id}")
def update_rule(request, rule_id: int, payload: TaxRuleUpdateSchema):
    store = _store(request)
    data = {k: v for k, v in payload.dict().items() if v is not None}
    try:
        rule = service.update_rule(store, rule_id, data)
        return service.serialize_rule(rule)
    except TaxError as e:
        raise HttpError(400, str(e))


@router.delete("/rules/{rule_id}")
def delete_rule(request, rule_id: int):
    store = _store(request)
    try:
        service.delete_rule(store, rule_id)
        return {"success": True}
    except TaxError as e:
        raise HttpError(404, str(e))
