"""Security audit logging service."""

import logging

from core.enums import AuditAction, AuditOutcome
from core.models import AuditLog
from core.utils.request import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)


class AuditService:
    """Persist security-relevant events without interrupting request flow."""

    def log(
        self,
        action: str,
        *,
        request=None,
        user=None,
        store=None,
        outcome: str = AuditOutcome.SUCCESS,
        resource_type: str = "",
        resource_id: str = "",
        metadata: dict | None = None,
    ) -> AuditLog | None:
        try:
            if request and not user and getattr(request, "auth", None):
                user = request.auth
            if request and not store:
                store = getattr(request, "store", None)

            ip_address = get_client_ip(request) if request else None
            user_agent = get_user_agent(request) if request else ""

            return AuditLog.objects.create(
                store=store,
                user=user,
                action=action,
                outcome=outcome,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else "",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata=metadata or {},
            )
        except Exception as exc:
            logger.warning("Audit log write failed: %s", exc)
            return None

    def log_login(self, request, user, store=None, *, success: bool = True, metadata: dict | None = None):
        return self.log(
            AuditAction.LOGIN,
            request=request,
            user=user,
            store=store,
            outcome=AuditOutcome.SUCCESS if success else AuditOutcome.FAILURE,
            metadata=metadata,
        )

    def log_logout(self, request, user=None, store=None):
        return self.log(AuditAction.LOGOUT, request=request, user=user, store=store)

    def log_register(self, request, user, store=None):
        return self.log(AuditAction.REGISTER, request=request, user=user, store=store)

    def log_rate_limited(self, request, scope: str, identifier: str):
        return self.log(
            AuditAction.RATE_LIMITED,
            request=request,
            outcome=AuditOutcome.BLOCKED,
            metadata={"scope": scope, "identifier": identifier},
        )
