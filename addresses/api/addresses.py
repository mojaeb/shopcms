"""Address API endpoints."""

from ninja import Router, Schema
from ninja.errors import HttpError

from accounts.models import User
from accounts.services.jwt import JWTService
from addresses.services.address import AddressError, AddressService
from core.utils.geo import is_iran_coordinate
from tenants.context import get_current_store

router = Router()
service = AddressService()


class AddressSchema(Schema):
    full_name: str
    phone: str
    province: str
    city: str
    postal_code: str
    address_line: str
    building_no: str = ""
    unit: str = ""
    label: str = ""
    is_default: bool = False
    latitude: float | None = None
    longitude: float | None = None


class AddressUpdateSchema(Schema):
    full_name: str | None = None
    phone: str | None = None
    province: str | None = None
    city: str | None = None
    postal_code: str | None = None
    address_line: str | None = None
    building_no: str | None = None
    unit: str | None = None
    label: str | None = None
    is_default: bool | None = None
    latitude: float | None = None
    longitude: float | None = None


class AddressResponseSchema(Schema):
    id: int
    full_name: str
    phone: str
    province: str
    city: str
    postal_code: str
    address_line: str
    building_no: str
    unit: str
    label: str
    is_default: bool
    full_address: str
    latitude: float | None = None
    longitude: float | None = None


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


@router.get("/", response=list[AddressResponseSchema])
def list_addresses(request):
    store = _store(request)
    user = _user(request)
    return [service.serialize_address(a) for a in service.list_addresses(user, store)]


@router.get("/checkout-selection", response=AddressResponseSchema | None)
def checkout_selection(request):
    store = _store(request)
    user = _user(request)
    address = service.get_checkout_selection(user, store)
    return service.serialize_address(address) if address else None


@router.post("/", response=AddressResponseSchema)
def create_address(request, payload: AddressSchema):
    store = _store(request)
    user = _user(request)
    data = payload.dict()
    lat = data.get("latitude")
    lng = data.get("longitude")
    if lat is not None and lng is not None:
        if not is_iran_coordinate(lat, lng):
            raise HttpError(400, "موقعیت انتخابی خارج از محدوده‌ی جغرافیایی ایران است")
    try:
        address = service.create_address(user, store, data)
        return service.serialize_address(address)
    except AddressError as e:
        raise HttpError(400, str(e))


@router.get("/{address_id}", response=AddressResponseSchema)
def get_address(request, address_id: int):
    store = _store(request)
    user = _user(request)
    try:
        return service.serialize_address(service.get_address(user, store, address_id))
    except AddressError as e:
        raise HttpError(404, str(e))


@router.put("/{address_id}", response=AddressResponseSchema)
def update_address(request, address_id: int, payload: AddressUpdateSchema):
    store = _store(request)
    user = _user(request)
    data = {k: v for k, v in payload.dict().items() if v is not None}
    lat = data.get("latitude")
    lng = data.get("longitude")
    if lat is not None and lng is not None:
        if not is_iran_coordinate(lat, lng):
            raise HttpError(400, "موقعیت انتخابی خارج از محدوده‌ی جغرافیایی ایران است")
    try:
        address = service.update_address(user, store, address_id, data)
        return service.serialize_address(address)
    except AddressError as e:
        raise HttpError(400, str(e))


@router.delete("/{address_id}")
def delete_address(request, address_id: int):
    store = _store(request)
    user = _user(request)
    try:
        service.delete_address(user, store, address_id)
        return {"detail": "آدرس حذف شد"}
    except AddressError as e:
        raise HttpError(404, str(e))


@router.post("/{address_id}/set-default", response=AddressResponseSchema)
def set_default_address(request, address_id: int):
    store = _store(request)
    user = _user(request)
    try:
        address = service.set_default(user, store, address_id)
        return service.serialize_address(address)
    except AddressError as e:
        raise HttpError(404, str(e))
