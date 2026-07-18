"""Public shipping API."""

from ninja import Router, Schema

from addresses.services.address import AddressService
from shipping.services.shipping import ShippingService
from tenants.context import get_current_store

router = Router()
service = ShippingService()
address_service = AddressService()


class ShippingCalculateSchema(Schema):
    province: str = ""
    city: str = ""
    address_id: int | None = None


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
