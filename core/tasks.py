"""Celery tasks for core application."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def ping(self):
    """Simple task to verify Celery is working."""
    logger.info("Celery ping task executed")
    return "pong"


@shared_task
def cleanup_temp_files(max_age_hours: int = 24):
    """Remove stale temporary upload files."""
    from core.services.maintenance import MaintenanceService

    result = MaintenanceService().cleanup_temp_files(max_age_hours=max_age_hours)
    logger.info("Cleanup temp files completed: %s", result)
    return result


@shared_task
def expire_subscriptions(store_slug: str | None = None):
    """Expire past-due subscriptions across stores."""
    from subscriptions.services.subscription import SubscriptionService

    service = SubscriptionService()
    if store_slug:
        from tenants.models import Store

        store = Store.objects.get(slug=store_slug)
        count = service.expire_due_subscriptions(store=store)
    else:
        count = service.expire_due_subscriptions()
    logger.info("Expired subscriptions: %s", count)
    return {"expired": count}


@shared_task
def warm_active_stores_cache(store_slug: str | None = None):
    """Warm store and product filter caches."""
    from core.services.maintenance import MaintenanceService

    result = MaintenanceService().warm_active_stores(store_slug=store_slug)
    logger.info("Cache warmup completed for %s stores", result["warmed_stores"])
    return result


@shared_task
def backup_active_stores(store_slug: str | None = None):
    """Create nightly backups for active stores."""
    from core.services.backup import BackupService
    from tenants.enums import StoreStatus
    from tenants.models import Store

    service = BackupService()
    qs = Store.objects.filter(status=StoreStatus.ACTIVE)
    if store_slug:
        qs = qs.filter(slug=store_slug)

    completed = 0
    for store in qs:
        service.create_store_backup(store, include_media=True)
        completed += 1
    logger.info("Store backups completed: %s", completed)
    return {"completed": completed}


@shared_task
def cleanup_old_backups(retention_days: int | None = None):
    """Remove backup archives older than retention policy."""
    from core.services.backup import BackupService

    result = BackupService().cleanup_old_backups(retention_days=retention_days)
    logger.info("Old backups cleanup: %s", result)
    return result


@shared_task
def cleanup_audit_logs(retention_days: int | None = None):
    """Remove old security audit logs."""
    from datetime import timedelta

    from django.conf import settings
    from django.utils import timezone

    from core.models import AuditLog

    days = retention_days or getattr(settings, "AUDIT_LOG_RETENTION_DAYS", 90)
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
    logger.info("Audit log cleanup removed %s rows", deleted)
    return {"removed": deleted, "retention_days": days}
