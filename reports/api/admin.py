"""Store admin reports API."""

from ninja import Router

from dashboard.authentication_store import store_reports_auth
from reports.services.report import ReportService
from tenants.context import get_current_store
from ninja.errors import HttpError

router = Router(auth=store_reports_auth)
service = ReportService()


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/summary")
def reports_summary(request, days: int = 30):
    return service.get_summary(_store(request), days=days)


@router.get("/sales")
def sales_report(request, days: int = 30):
    return service.get_sales_report(_store(request), days=days)


@router.get("/customers")
def customers_report(request, days: int = 30):
    return service.get_customers_report(_store(request), days=days)


@router.get("/products")
def products_report(request, days: int = 30):
    return service.get_products_report(_store(request), days=days)


@router.get("/inventory")
def inventory_report(request):
    return service.get_inventory_report(_store(request))


@router.get("/payments")
def payments_report(request, days: int = 30):
    return service.get_payments_report(_store(request), days=days)


@router.get("/shipping")
def shipping_report(request, days: int = 30):
    return service.get_shipping_report(_store(request), days=days)
