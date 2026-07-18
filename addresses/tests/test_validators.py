"""Validator unit tests."""

import pytest

from addresses.validators import AddressValidationError, validate_address_data


def test_validate_address_success():
    data = validate_address_data({
        "full_name": "Ali",
        "phone": "09123456789",
        "province": "Tehran",
        "city": "Tehran",
        "postal_code": "1234567890",
        "address_line": "Street 1",
    })
    assert data["phone"] == "09123456789"


def test_validate_address_invalid_phone():
    with pytest.raises(AddressValidationError):
        validate_address_data({
            "full_name": "Ali",
            "phone": "1234",
            "province": "Tehran",
            "city": "Tehran",
            "postal_code": "1234567890",
            "address_line": "Street 1",
        })
