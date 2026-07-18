"""Address validators."""

import re

from accounts.managers import UserManager

POSTAL_CODE_RE = re.compile(r"^\d{10}$")
PHONE_RE = re.compile(r"^09\d{9}$")


class AddressValidationError(Exception):
    pass


def normalize_phone(phone: str) -> str:
    return UserManager.normalize_phone(phone)


def normalize_postal_code(postal_code: str) -> str:
    return postal_code.strip().replace("-", "").replace(" ", "")


def validate_address_data(data: dict, partial: bool = False) -> dict:
    required = ["full_name", "phone", "province", "city", "postal_code", "address_line"]
    if not partial:
        for field in required:
            if not str(data.get(field, "")).strip():
                raise AddressValidationError(f"فیلد {field} الزامی است")

    cleaned = dict(data)
    if "phone" in cleaned and cleaned["phone"]:
        phone = normalize_phone(str(cleaned["phone"]))
        if not PHONE_RE.match(phone):
            raise AddressValidationError("شماره موبایل نامعتبر است")
        cleaned["phone"] = phone

    if "postal_code" in cleaned and cleaned["postal_code"]:
        postal_code = normalize_postal_code(str(cleaned["postal_code"]))
        if not POSTAL_CODE_RE.match(postal_code):
            raise AddressValidationError("کد پستی باید ۱۰ رقم باشد")
        cleaned["postal_code"] = postal_code

    for field in ("full_name", "province", "city", "address_line", "building_no", "unit"):
        if field in cleaned and cleaned[field] is not None:
            cleaned[field] = str(cleaned[field]).strip()

    return cleaned
