"""Public shipping API."""

from ninja import Router, Schema

from addresses.services.address import AddressService
from core.utils.geo import is_iran_coordinate
from shipping.distance import real_distance_km
from shipping.services.shipping import ShippingService
from tenants.context import get_current_store

router = Router()
service = ShippingService()
address_service = AddressService()


class ShippingCalculateSchema(Schema):
    province: str = ""
    city: str = ""
    address_id: int | None = None


class DistancePreviewSchema(Schema):
    latitude: float
    longitude: float


@router.get("/methods")
def list_methods(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    return service.list_methods(store)


@router.post("/calculate")
def calculate_shipping(request, payload: ShippingCalculateSchema):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}

    province = payload.province
    city = payload.city

    if payload.address_id:
        from accounts.models import User
        from accounts.services.jwt import JWTService

        user = None
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token_payload = JWTService().verify_access_token(auth_header[7:])
            if token_payload:
                user = User.objects.filter(pk=int(token_payload["sub"]), is_active=True).first()
        if not user and request.user.is_authenticated:
            user = request.user
        if user:
            try:
                address = address_service.get_address(user, store, payload.address_id)
                province = address.province
                city = address.city
            except Exception:
                return 400, {"detail": "آدرس نامعتبر است"}

    if not city:
        return 400, {"detail": "شهر مقصد الزامی است"}

    quotes = service.get_quotes(store, province, city, request=request)
    return {
        "quotes": [service.serialize_quote(q) for q in quotes],
        "weight_kg": str(service.build_context(store, province, city, request=request).weight_kg),
    }


@router.post("/distance-preview")
def distance_preview(request, payload: DistancePreviewSchema):
    """Return straight-line (or routed) km from store origin to given coordinates.

    معادل route پی‌اچ‌پی: pws/map/distance/
    """
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}

    lat = payload.latitude
    lng = payload.longitude

    if not is_iran_coordinate(lat, lng):
        return 400, {"detail": "موقعیت انتخابی خارج از محدوده‌ی جغرافیایی ایران است"}

    origin_lat = getattr(store, "origin_latitude", None)
    origin_lng = getattr(store, "origin_longitude", None)
    if origin_lat is None or origin_lng is None:
        return 400, {"detail": "مختصات مبدا فروشگاه تنظیم نشده است"}

    api_key = service._routing_api_key(store)
    distance = real_distance_km(
        float(origin_lat), float(origin_lng),
        lat, lng,
        api_key=api_key,
        store_id=store.pk,
    )
    return {"distance_km": str(distance)}
