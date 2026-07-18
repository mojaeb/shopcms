"""Store admin security audit API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from core.models import AuditLog
from dashboard.authentication_store import store_security_auth
from tenants.context import get_current_store

router = Router(auth=store_security_auth)


class AuditLogSchema(Schema):
    id: int
    action: str
    outcome: str
    user_id: int | None
    resource_type: str
    resource_id: str
    ip_address: str | None
    user_agent: str
    metadata: dict
    created_at: str


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


def _to_schema(log: AuditLog) -> AuditLogSchema:
    return AuditLogSchema(
        id=log.id,
        action=log.action,
        outcome=log.outcome,
        user_id=log.user_id,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        metadata=log.metadata,
        created_at=log.created_at.isoformat(),
    )


@router.get("/", response=list[AuditLogSchema])
def list_audit_logs(request, action: str | None = None, limit: int = 50):
    store = _store(request)
    qs = AuditLog.objects.filter(store=store).select_related("user").order_by("-created_at")
    if action:
        qs = qs.filter(action=action)
    return [_to_schema(item) for item in qs[: min(limit, 200)]]
