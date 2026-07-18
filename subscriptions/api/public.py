"""Customer subscription API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.models import User
from accounts.services.jwt import JWTService
from subscriptions.services.subscription import SubscriptionError, SubscriptionService
from tenants.context import get_current_store

router = Router()
service = SubscriptionService()


class CancelSchema(Schema):
    immediate: bool = False


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


def _user(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Bearer "):
        payload = JWTService().verify_access_token(auth_header[7:])
        if payload:
            user = User.objects.filter(pk=int(payload["sub"]), is_active=True).first()
            if user:
                return user
    if getattr(request, "user", None) and request.user.is_authenticated:
        return request.user
    raise HttpError(401, "ورود الزامی است")


@router.get("/")
def list_subscriptions(request):
    store = _store(request)
    if not service.is_active(store):
        return []
    user = _user(request)
    subs = service.list_user_subscriptions(user, store)
    return [service.serialize_subscription(s) for s in subs]


@router.post("/{subscription_id}/cancel")
def cancel_subscription(request, subscription_id: int, payload: CancelSchema):
    store = _store(request)
    user = _user(request)
    from subscriptions.models import CustomerSubscription

    try:
        sub = CustomerSubscription.objects.get(pk=subscription_id, store=store, user=user)
    except CustomerSubscription.DoesNotExist:
        raise HttpError(404, "اشتراک یافت نشد")
    try:
        sub = service.cancel(sub, immediate=payload.immediate)
        return service.serialize_subscription(sub)
    except SubscriptionError as exc:
        raise HttpError(400, str(exc))


@router.post("/{subscription_id}/renew")
def renew_subscription(request, subscription_id: int):
    store = _store(request)
    user = _user(request)
    from subscriptions.models import CustomerSubscription

    try:
        sub = CustomerSubscription.objects.get(pk=subscription_id, store=store, user=user)
    except CustomerSubscription.DoesNotExist:
        raise HttpError(404, "اشتراک یافت نشد")
    try:
        sub = service.renew(sub, payment_ref="manual")
        return service.serialize_subscription(sub)
    except SubscriptionError as exc:
        raise HttpError(400, str(exc))
