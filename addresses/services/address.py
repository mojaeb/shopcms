"""Address service layer."""

from django.db import transaction

from addresses.models import CustomerAddress
from addresses.validators import AddressValidationError, validate_address_data


class AddressError(Exception):
    pass


class AddressService:
    """CRUD and selection logic for customer addresses."""

    def list_addresses(self, user, store):
        return CustomerAddress.objects.filter(user=user, store=store)

    def get_address(self, user, store, address_id: int) -> CustomerAddress:
        try:
            return CustomerAddress.objects.get(pk=address_id, user=user, store=store)
        except CustomerAddress.DoesNotExist:
            raise AddressError("آدرس یافت نشد")

    @transaction.atomic
    def create_address(self, user, store, data: dict) -> CustomerAddress:
        try:
            cleaned = validate_address_data(data)
        except AddressValidationError as e:
            raise AddressError(str(e))

        is_default = cleaned.pop("is_default", False)
        if is_default or not self.list_addresses(user, store).exists():
            is_default = True

        if is_default:
            self._clear_defaults(user, store)

        return CustomerAddress.objects.create(
            user=user,
            store=store,
            is_default=is_default,
            **cleaned,
        )

    @transaction.atomic
    def update_address(self, user, store, address_id: int, data: dict) -> CustomerAddress:
        address = self.get_address(user, store, address_id)
        try:
            cleaned = validate_address_data(data, partial=True)
        except AddressValidationError as e:
            raise AddressError(str(e))

        is_default = cleaned.pop("is_default", None)
        for field, value in cleaned.items():
            setattr(address, field, value)

        if is_default is True:
            self._clear_defaults(user, store, exclude_id=address.pk)
            address.is_default = True
        elif is_default is False and address.is_default:
            address.is_default = False

        address.save()
        if not self.list_addresses(user, store).filter(is_default=True).exists():
            first = self.list_addresses(user, store).first()
            if first:
                first.is_default = True
                first.save(update_fields=["is_default", "updated_at"])

        return address

    @transaction.atomic
    def delete_address(self, user, store, address_id: int) -> None:
        address = self.get_address(user, store, address_id)
        was_default = address.is_default
        address.delete()

        if was_default:
            first = self.list_addresses(user, store).first()
            if first:
                first.is_default = True
                first.save(update_fields=["is_default", "updated_at"])

    @transaction.atomic
    def set_default(self, user, store, address_id: int) -> CustomerAddress:
        address = self.get_address(user, store, address_id)
        self._clear_defaults(user, store, exclude_id=address.pk)
        address.is_default = True
        address.save(update_fields=["is_default", "updated_at"])
        return address

    def get_checkout_selection(self, user, store) -> CustomerAddress | None:
        """Auto-select if one address; if multiple, only return explicit default."""
        addresses = list(self.list_addresses(user, store))
        if len(addresses) == 1:
            return addresses[0]
        if len(addresses) >= 2:
            return next((a for a in addresses if a.is_default), None)
        return None

    def serialize_address(self, address: CustomerAddress) -> dict:
        lat = address.latitude
        lng = address.longitude
        return {
            "id": address.id,
            "full_name": address.full_name,
            "phone": address.phone,
            "province": address.province,
            "city": address.city,
            "postal_code": address.postal_code,
            "address_line": address.address_line,
            "building_no": address.building_no,
            "unit": address.unit,
            "label": address.label,
            "is_default": address.is_default,
            "full_address": address.full_address,
            "latitude": float(lat) if lat is not None else None,
            "longitude": float(lng) if lng is not None else None,
        }

    def _clear_defaults(self, user, store, exclude_id: int | None = None):
        qs = CustomerAddress.objects.filter(user=user, store=store, is_default=True)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        qs.update(is_default=False)
