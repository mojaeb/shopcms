"""Payment API endpoints."""

from decimal import Decimal

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.models import User
from accounts.services.jwt import JWTService
from dashboard.authentication_store import store_settings_auth
from payments.enums import PaymentStatus
from payments.models import PaymentTransaction
from payments.services.payment import PaymentError, PaymentService
from tenants.context import get_current_store

router = Router()
service = PaymentService()


class PaymentCreateSchema(Schema):
    gateway: str
    address_id: int
    shipping_method_id: int
    shipping_price: float


class RefundSchema(Schema):
    amount: float | None = None


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


@router.get("/gateways")
def list_gateways(request):
    store = _store(request)
    return service.get_store_gateways(store)


@router.post("/create")
def create_payment(request, payload: PaymentCreateSchema):
    store = _store(request)
    user = _user(request)
    try:
        txn = service.create_payment(
            store,
            user,
            payload.gateway,
            payload.address_id,
            payload.shipping_method_id,
            Decimal(str(payload.shipping_price)),
            request,
        )
        return service.serialize_transaction(txn)
    except PaymentError as e:
        raise HttpError(400, str(e))


@router.get("/callback/{gateway}/")
def payment_callback(request, gateway: str, Authority: str = "", Status: str = "", status: str = ""):
    store = _store(request)
    params = dict(request.GET.items())
    if not Authority:
        Authority = params.get("Authority", params.get("authority", ""))

    txn = PaymentTransaction.objects.filter(store=store, gateway=gateway, authority=Authority).first()
    if not txn:
        return HttpResponseRedirect("/order/success/?status=failed")

    txn = service.verify_payment(txn, params)
    if txn.status == PaymentStatus.PAID:
        order_number = txn.metadata.get("order_number", "")
        url = f"/order/success/?tracking={txn.tracking_code}&ref={txn.ref_id}"
        if order_number:
            url += f"&order={order_number}"
        return HttpResponseRedirect(url)
    return HttpResponseRedirect(f"/order/success/?status=failed&tracking={txn.tracking_code}")


@router.post("/webhook/{gateway}/")
def payment_webhook(request, gateway: str, payload: dict):
    store = _store(request)
    txn = service.handle_webhook(store, gateway, payload)
    if not txn:
        raise HttpError(404, "تراکنش یافت نشد")
    return service.serialize_transaction(txn)


@router.get("/{tracking_code}")
def get_payment(request, tracking_code: str):
    store = _store(request)
    txn = get_object_or_404(PaymentTransaction, store=store, tracking_code=tracking_code)
    return service.serialize_transaction(txn)


@router.post("/{tracking_code}/verify")
def verify_payment_manual(request, tracking_code: str, payload: dict):
    store = _store(request)
    txn = get_object_or_404(PaymentTransaction, store=store, tracking_code=tracking_code)
    txn = service.verify_payment(txn, payload)
    return service.serialize_transaction(txn)


@router.post("/{tracking_code}/refund", auth=store_settings_auth)
def refund_payment(request, tracking_code: str, payload: RefundSchema):
    store = _store(request)
    txn = get_object_or_404(PaymentTransaction, store=store, tracking_code=tracking_code)
    try:
        amount = Decimal(str(payload.amount)) if payload.amount is not None else None
        txn = service.refund_payment(txn, amount)
        return service.serialize_transaction(txn)
    except PaymentError as e:
        raise HttpError(400, str(e))
