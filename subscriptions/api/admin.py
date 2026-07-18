"""Store admin subscription API."""

from decimal import Decimal

from ninja import Router, Schema
from ninja.errors import HttpError

from dashboard.authentication_store import store_products_auth
from subscriptions.enums import BillingInterval
from subscriptions.models import CustomerSubscription
from subscriptions.services.subscription import SubscriptionError, SubscriptionService
from tenants.context import get_current_store

router = Router(auth=store_products_auth)
service = SubscriptionService()


class PlanCreateSchema(Schema):
    interval: str = BillingInterval.MONTHLY
    interval_count: int = 1
    trial_days: int = 0
    grace_period_days: int = 3
    price: float = 0


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/products/{product_id}/plan")
def get_plan(request, product_id: int):
    store = _store(request)
    plan = service.get_plan(store, product_id)
    if not plan:
        return None
    return service.serialize_plan(plan)


@router.post("/products/{product_id}/plan")
def create_plan(request, product_id: int, payload: PlanCreateSchema):
    store = _store(request)
    if payload.interval not in BillingInterval.values:
        raise HttpError(400, "دوره نامعتبر است")
    plan = service.create_plan(
        store,
        product_id,
        payload.interval,
        Decimal(str(payload.price)),
        interval_count=payload.interval_count,
        trial_days=payload.trial_days,
        grace_period_days=payload.grace_period_days,
    )
    return service.serialize_plan(plan)


@router.get("/list")
def list_subscriptions(request, status: str | None = None):
    store = _store(request)
    subs = service.list_store_subscriptions(store, status=status)
    return [
        {
            **service.serialize_subscription(s),
            "user_phone": s.user.phone,
            "user_name": s.user.full_name,
        }
        for s in subs[:100]
    ]


@router.post("/{subscription_id}/renew")
def admin_renew(request, subscription_id: int):
    store = _store(request)
    try:
        sub = CustomerSubscription.objects.get(pk=subscription_id, store=store)
    except CustomerSubscription.DoesNotExist:
        raise HttpError(404, "اشتراک یافت نشد")
    try:
        sub = service.renew(sub, payment_ref="admin")
        return service.serialize_subscription(sub)
    except SubscriptionError as exc:
        raise HttpError(400, str(exc))
