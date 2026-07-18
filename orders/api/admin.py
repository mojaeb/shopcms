"""Store admin orders API."""

from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination, paginate

from dashboard.authentication_store import store_orders_auth
from orders.enums import OrderStatus
from orders.services.order import OrderError, OrderService
from tenants.context import get_current_store

router = Router(auth=store_orders_auth)
service = OrderService()


class OrderAdminListSchema(Schema):
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
    shipping_method: str
    address: dict
    item_count: int
    created_at: str
    user: dict


class OrderAdminDetailSchema(OrderAdminListSchema):
    items: list
    customer_note: str
    shipment: dict | None = None
    history: list
    invoice: dict | None = None
    payment: dict | None = None


class OrderStatusUpdateSchema(Schema):
    status: str
    note: str = ""


class ShipmentUpdateSchema(Schema):
    tracking_code: str = ""
    carrier: str = ""
    status: str | None = None


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/", response=list[OrderAdminListSchema])
@paginate(PageNumberPagination, page_size=20)
def list_orders(request, status: str | None = None):
    store = _store(request)
    qs = service.list_store_orders(store, status=status)
    return [service.serialize_order_admin(o) for o in qs]


@router.get("/{order_id}", response=OrderAdminDetailSchema)
def get_order(request, order_id: int):
    store = _store(request)
    try:
        order = service.get_store_order(store, order_id)
        return service.serialize_order_admin(order)
    except OrderError as e:
        raise HttpError(404, str(e))


@router.put("/{order_id}/status")
def update_status(request, order_id: int, payload: OrderStatusUpdateSchema):
    store = _store(request)
    try:
        order = service.get_store_order(store, order_id)
        order = service.update_status(
            order,
            payload.status,
            payload.note,
            getattr(request, "auth", None),
        )
        return service.serialize_order_admin(order)
    except OrderError as e:
        raise HttpError(400, str(e))


@router.put("/{order_id}/shipment")
def update_shipment(request, order_id: int, payload: ShipmentUpdateSchema):
    store = _store(request)
    try:
        order = service.get_store_order(store, order_id)
        shipment = service.update_shipment(
            order,
            payload.tracking_code,
            payload.carrier,
            payload.status,
        )
        return {
            "status": shipment.status,
            "tracking_code": shipment.tracking_code,
            "carrier": shipment.carrier,
        }
    except OrderError as e:
        raise HttpError(400, str(e))


@router.get("/meta/statuses")
def order_statuses(request):
    return [{"value": v, "label": l} for v, l in OrderStatus.choices]
