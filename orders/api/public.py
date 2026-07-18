"""Customer order API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.models import User
from accounts.services.jwt import JWTService
from orders.services.order import OrderError, OrderService
from tenants.context import get_current_store

router = Router()
service = OrderService()


class OrderListSchema(Schema):
    id: int
    order_number: str
    status: str
    status_label: str
    subtotal: str
    discount: str
    shipping_cost: str
    tax: str
    total: str
    coupon_code: str
    gift_card_code: str = ""
    shipping_method: str
    address: dict
    item_count: int
    created_at: str


class OrderDetailSchema(OrderListSchema):
    items: list
    customer_note: str
    shipment: dict | None = None
    history: list
    invoice: dict | None = None
    payment: dict | None = None


class InvoiceSchema(Schema):
    invoice_number: str
    order_number: str
    issued_at: str
    pdf_url: str
    pdf_available: bool
    message: str
    totals: dict
    items: list
    address: dict


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


@router.get("/", response=list[OrderListSchema])
def list_orders(request):
    store = _store(request)
    user = _user(request)
    orders = service.list_customer_orders(user, store)
    return [service.serialize_order(o) for o in orders]


@router.get("/{order_id}", response=OrderDetailSchema)
def get_order(request, order_id: int):
    store = _store(request)
    user = _user(request)
    try:
        order = service.get_customer_order(user, store, order_id)
        return service.serialize_order(order, detailed=True)
    except OrderError as e:
        raise HttpError(404, str(e))


@router.get("/{order_id}/invoice", response=InvoiceSchema)
def get_invoice(request, order_id: int):
    store = _store(request)
    user = _user(request)
    try:
        order = service.get_customer_order(user, store, order_id)
        return service.serialize_invoice(order)
    except OrderError as e:
        raise HttpError(404, str(e))
