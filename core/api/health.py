"""Health check API endpoints."""

from ninja import Router

from core.services.health import HealthService

router = Router()


@router.get("/")
def health_check(request):
    """Platform health check endpoint."""
    service = HealthService()
    status = service.get_status()
    return {
        "status": status.status,
        "database": status.database,
        "cache": status.cache,
        "cache_backend": status.cache_backend,
        "celery": status.celery,
        "version": status.version,
    }


@router.get("/live")
def liveness(request):
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@router.get("/ready")
def readiness(request):
    """Kubernetes readiness probe."""
    service = HealthService()
    status = service.get_status()
    if status.status != "healthy":
        return 503, {"status": "not_ready", "database": status.database, "cache": status.cache}
    return {"status": "ready"}


@router.get("/metrics")
def platform_metrics(request):
    """Basic platform metrics for monitoring dashboards."""
    from django.contrib.auth import get_user_model

    from orders.models import Order
    from tenants.models import Store

    User = get_user_model()
    return {
        "stores_active": Store.objects.filter(status="active").count(),
        "stores_total": Store.objects.count(),
        "users_total": User.objects.count(),
        "orders_total": Order.objects.count(),
    }
