"""Structured store configuration helpers for Unfold admin."""

from __future__ import annotations

import json
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction

from cms.models import LayoutSettings
from tenants.models import Store, StoreSetting
from tenants.services.cache import StoreCacheService
from tenants.services.theme_settings import ThemeSettingsService, normalize_theme_config

CONTACT_GROUP = "contact"
SEO_GROUP = "seo"
PAYMENT_GROUP = "payment"
SHIPPING_GROUP = "shipping"
TAX_GROUP = "tax"
STORAGE_GROUP = "storage"
NOTIFICATIONS_GROUP = "notifications"

CONTACT_KEYS = (
    "phone",
    "email",
    "address",
    "whatsapp",
    "instagram",
    "telegram",
    "twitter",
    "linkedin",
    "youtube",
)

SEO_KEYS = (
    "meta_title",
    "meta_description",
    "meta_keywords",
    "og_image",
    "robots",
    "canonical_url",
)

# Keys edited via StoreConfigForm — hide from the raw JSON inline to avoid
# Django JSONField rejecting stored empty strings ("") as "required".
STRUCTURED_ADMIN_SETTING_KEYS: frozenset[tuple[str, str]] = frozenset(
    {
        *((CONTACT_GROUP, key) for key in CONTACT_KEYS),
        *((SEO_GROUP, key) for key in SEO_KEYS),
        (SEO_GROUP, "google_site_verification"),
        (SEO_GROUP, "google_html_file"),
        (TAX_GROUP, "on_shipping"),
        (PAYMENT_GROUP, "gateways"),
        (PAYMENT_GROUP, "default_gateway"),
        (PAYMENT_GROUP, "callback_base_url"),
        (PAYMENT_GROUP, "zarinpal"),
        (PAYMENT_GROUP, "idpay"),
        (PAYMENT_GROUP, "mellat"),
        (PAYMENT_GROUP, "pasargad"),
        (PAYMENT_GROUP, "sina"),
        (SHIPPING_GROUP, "origin"),
        (SHIPPING_GROUP, "free_shipping_threshold"),
        (SHIPPING_GROUP, "default_provider"),
        (SHIPPING_GROUP, "providers"),
        (SHIPPING_GROUP, "base_package_weight_kg"),
        (SHIPPING_GROUP, "post"),
        (SHIPPING_GROUP, "tipax"),
        (SHIPPING_GROUP, "peyk"),
        (STORAGE_GROUP, "driver"),
        (NOTIFICATIONS_GROUP, "sms"),
    }
)


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_decimal_str(value: Any, default: str = "0") -> str:
    if value in (None, ""):
        return default
    try:
        return str(Decimal(str(value)))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _pretty_json(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def _parse_json_object(raw: Any) -> dict[str, Any] | None:
    if raw in (None, ""):
        return None
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(str(raw))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _json_equivalent(left: Any, right: Any) -> bool:
    try:
        return json.dumps(left, sort_keys=True, default=str) == json.dumps(
            right, sort_keys=True, default=str
        )
    except (TypeError, ValueError):
        return left == right


def _parse_json_array(raw: Any) -> list[Any] | None:
    if raw in (None, ""):
        return None
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(str(raw))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, list) else None


def _as_number(value: Any, *, as_int: bool = False) -> Any:
    if value in (None, ""):
        return 0 if as_int else 0
    try:
        dec = Decimal(str(value))
        if as_int or dec == dec.to_integral_value():
            return int(dec)
        return float(dec)
    except (InvalidOperation, TypeError, ValueError):
        return 0


def _cities_from_csv(raw: Any) -> list[str]:
    text = _as_str(raw)
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def _get_setting(store: Store, group: str, key: str, default: Any = None) -> Any:
    row = StoreSetting.objects.filter(store=store, group=group, key=key).first()
    if row is None:
        return deepcopy(default) if default is not None else None
    return row.value


def _set_setting(
    store: Store,
    group: str,
    key: str,
    value: Any,
    *,
    description: str = "",
) -> None:
    StoreSetting.objects.update_or_create(
        store=store,
        group=group,
        key=key,
        defaults={
            "value": value,
            "value_type": "json",
            "description": description,
        },
    )


class StoreConfigService:
    """Load/save store settings as flat admin-friendly values."""

    def __init__(self):
        self.cache_service = StoreCacheService()
        self.theme_service = ThemeSettingsService()

    def get_admin_initial(self, store: Store | None) -> dict[str, Any]:
        if not store or not store.pk:
            return self._empty_initial()

        theme = self.theme_service.get_theme_settings(store)
        colors = theme.get("colors") or {}
        trust = theme.get("trust_badges") or {}
        enamad = trust.get("enamad") or {}
        badge2 = trust.get("badge2") or {}

        contact = {k: _as_str(_get_setting(store, CONTACT_GROUP, k, "")) for k in CONTACT_KEYS}
        seo = {k: _as_str(_get_setting(store, SEO_GROUP, k, "")) for k in SEO_KEYS}
        if not seo["robots"]:
            seo["robots"] = "index,follow"

        payment = self._group_map(store, PAYMENT_GROUP)
        zarinpal = payment.get("zarinpal") if isinstance(payment.get("zarinpal"), dict) else {}
        idpay = payment.get("idpay") if isinstance(payment.get("idpay"), dict) else {}
        mellat = payment.get("mellat") if isinstance(payment.get("mellat"), dict) else {}
        pasargad = payment.get("pasargad") if isinstance(payment.get("pasargad"), dict) else {}
        sina = payment.get("sina") if isinstance(payment.get("sina"), dict) else {}
        gateways = payment.get("gateways") or []
        if not isinstance(gateways, list):
            gateways = []

        shipping = self._group_map(store, SHIPPING_GROUP)
        origin = shipping.get("origin") if isinstance(shipping.get("origin"), dict) else {}
        ship_post = shipping.get("post") if isinstance(shipping.get("post"), dict) else {}
        ship_tipax = shipping.get("tipax") if isinstance(shipping.get("tipax"), dict) else {}
        ship_peyk = shipping.get("peyk") if isinstance(shipping.get("peyk"), dict) else {}
        threshold = shipping.get("free_shipping_threshold")
        if threshold is None:
            threshold = origin.get("free_shipping_threshold", 0)

        layout = LayoutSettings.objects.filter(store=store).first()
        hero_slides = (theme.get("hero") or {}).get("slides") if isinstance(theme.get("hero"), dict) else []
        if not isinstance(hero_slides, list):
            hero_slides = []
        peyk_cities = ship_peyk.get("delivery_cities") or []
        if isinstance(peyk_cities, list):
            peyk_cities_csv = ", ".join(str(c) for c in peyk_cities if c)
        else:
            peyk_cities_csv = _as_str(peyk_cities)

        notifications = self._group_map(store, NOTIFICATIONS_GROUP)
        sms = notifications.get("sms") if isinstance(notifications.get("sms"), dict) else {}

        return {
            "theme_logo": _as_str(theme.get("logo")),
            "theme_color_primary": _as_str(colors.get("primary"), "#0f766e"),
            "theme_color_background": _as_str(colors.get("background"), "#f8fafc"),
            "theme_color_text": _as_str(colors.get("text"), "#0f172a"),
            "trust_enamad_image": _as_str(enamad.get("image")),
            "trust_enamad_link": _as_str(enamad.get("link")),
            "trust_badge2_image": _as_str(badge2.get("image")),
            "trust_badge2_link": _as_str(badge2.get("link")),
            "contact_phone": contact["phone"],
            "contact_email": contact["email"],
            "contact_address": contact["address"],
            "contact_whatsapp": contact["whatsapp"],
            "social_instagram": contact["instagram"],
            "social_telegram": contact["telegram"],
            "social_twitter": contact["twitter"],
            "social_linkedin": contact["linkedin"],
            "social_youtube": contact["youtube"],
            "seo_meta_title": seo["meta_title"],
            "seo_meta_description": seo["meta_description"],
            "seo_meta_keywords": seo["meta_keywords"],
            "seo_og_image": seo["og_image"],
            "seo_robots": seo["robots"],
            "seo_canonical_url": seo["canonical_url"],
            "seo_google_site_verification": self._google_verification_display(store),
            "tax_on_shipping": _as_bool(_get_setting(store, TAX_GROUP, "on_shipping", False)),
            "payment_default_gateway": _as_str(payment.get("default_gateway")),
            "payment_gateways": [str(g) for g in gateways],
            "payment_callback_base_url": _as_str(payment.get("callback_base_url")),
            "zarinpal_merchant_id": _as_str(zarinpal.get("merchant_id")),
            "zarinpal_sandbox": _as_bool(zarinpal.get("sandbox"), True),
            "zarinpal_api_base": _as_str(zarinpal.get("api_base") or zarinpal.get("api_url")),
            "zarinpal_start_pay_url": _as_str(zarinpal.get("start_pay_url")),
            "zarinpal_graphql_url": _as_str(zarinpal.get("graphql_url")),
            "idpay_api_key": _as_str(idpay.get("api_key")),
            "idpay_sandbox": _as_bool(idpay.get("sandbox"), True),
            "idpay_use_json": False,
            "idpay_json": _pretty_json(idpay),
            "mellat_terminal_id": _as_str(mellat.get("terminal_id")),
            "mellat_username": _as_str(mellat.get("username")),
            "mellat_password": _as_str(mellat.get("password")),
            "mellat_sandbox": _as_bool(mellat.get("sandbox"), True),
            "mellat_use_json": False,
            "mellat_json": _pretty_json(mellat),
            "pasargad_merchant_code": _as_str(pasargad.get("merchant_code")),
            "pasargad_terminal_id": _as_str(pasargad.get("terminal_id")),
            "pasargad_sandbox": _as_bool(pasargad.get("sandbox"), True),
            "pasargad_use_json": False,
            "pasargad_json": _pretty_json(pasargad),
            "sina_terminal_id": _as_str(sina.get("terminal_id")),
            "sina_sandbox": _as_bool(sina.get("sandbox"), True),
            "sina_use_json": False,
            "sina_json": _pretty_json(sina),
            "shipping_origin_city": _as_str(origin.get("origin_city"), "مشهد"),
            "shipping_origin_province": _as_str(origin.get("origin_province"), "خراسان رضوی"),
            "shipping_providers": [str(p) for p in (shipping.get("providers") or []) if p],
            "shipping_free_threshold": _as_decimal_str(threshold, "0"),
            "shipping_default_provider": _as_str(shipping.get("default_provider")),
            "shipping_base_package_weight_kg": _as_decimal_str(
                shipping.get("base_package_weight_kg")
                if shipping.get("base_package_weight_kg") is not None
                else (origin.get("base_package_weight_kg") if isinstance(origin, dict) else None),
                "0",
            ),
            "ship_post_fixed_price": ship_post.get("fixed_price"),
            "ship_post_max_weight_kg": ship_post.get("max_weight_kg"),
            "ship_post_use_json": False,
            "ship_post_json": _pretty_json(ship_post),
            "ship_tipax_fixed_price": ship_tipax.get("fixed_price"),
            "ship_tipax_use_json": False,
            "ship_tipax_json": _pretty_json(ship_tipax),
            "ship_peyk_fixed_price": ship_peyk.get("fixed_price"),
            "ship_peyk_delivery_cities": peyk_cities_csv,
            "ship_peyk_use_json": False,
            "ship_peyk_json": _pretty_json(ship_peyk),
            "theme_hero_slides_json": _pretty_json(hero_slides) if hero_slides else "[]",
            "theme_hero_use_json": False,
            "storage_driver": _as_str(_get_setting(store, STORAGE_GROUP, "driver", "local"), "local"),
            "sms_otp_provider": _as_str(sms.get("provider"), "console_sms") or "console_sms",
            "sms_payamak_username": _as_str(sms.get("username")),
            "sms_payamak_password": "",
            "sms_payamak_body_id": _as_str(sms.get("body_id")),
            "sms_otp_template": _as_str(sms.get("otp_template")) or "کد ورود ShopCMS: {code}\nاعتبار: ۲ دقیقه",
            "layout_use_custom_header": bool(layout.use_custom_header) if layout else False,
            "layout_use_custom_footer": bool(layout.use_custom_footer) if layout else False,
            "layout_header_html": layout.header_html if layout else "",
            "layout_footer_html": layout.footer_html if layout else "",
        }

    @transaction.atomic
    def save_admin_data(self, store: Store, data: dict[str, Any]) -> None:
        self._save_theme(store, data)
        self._save_contact(store, data)
        self._save_seo(store, data)
        self._save_tax(store, data)
        self._save_payment(store, data)
        self._save_shipping(store, data)
        self._save_storage(store, data)
        self._save_sms(store, data)
        self._save_layout(store, data)
        self.cache_service.invalidate_store(store)

    def _empty_initial(self) -> dict[str, Any]:
        return {
            "theme_logo": "",
            "theme_color_primary": "#0f766e",
            "theme_color_background": "#f8fafc",
            "theme_color_text": "#0f172a",
            "trust_enamad_image": "",
            "trust_enamad_link": "",
            "trust_badge2_image": "",
            "trust_badge2_link": "",
            "contact_phone": "",
            "contact_email": "",
            "contact_address": "",
            "contact_whatsapp": "",
            "social_instagram": "",
            "social_telegram": "",
            "social_twitter": "",
            "social_linkedin": "",
            "social_youtube": "",
            "seo_meta_title": "",
            "seo_meta_description": "",
            "seo_meta_keywords": "",
            "seo_og_image": "",
            "seo_robots": "index,follow",
            "seo_canonical_url": "",
            "seo_google_site_verification": "",
            "tax_on_shipping": False,
            "payment_default_gateway": "",
            "payment_gateways": [],
            "payment_callback_base_url": "",
            "zarinpal_merchant_id": "",
            "zarinpal_sandbox": True,
            "zarinpal_api_base": "",
            "zarinpal_start_pay_url": "",
            "zarinpal_graphql_url": "",
            "idpay_api_key": "",
            "idpay_sandbox": True,
            "idpay_use_json": False,
            "idpay_json": "",
            "mellat_terminal_id": "",
            "mellat_username": "",
            "mellat_password": "",
            "mellat_sandbox": True,
            "mellat_use_json": False,
            "mellat_json": "",
            "pasargad_merchant_code": "",
            "pasargad_terminal_id": "",
            "pasargad_sandbox": True,
            "pasargad_use_json": False,
            "pasargad_json": "",
            "sina_terminal_id": "",
            "sina_sandbox": True,
            "sina_use_json": False,
            "sina_json": "",
            "shipping_origin_city": "مشهد",
            "shipping_origin_province": "خراسان رضوی",
            "shipping_providers": [],
            "shipping_free_threshold": "0",
            "shipping_default_provider": "",
            "shipping_base_package_weight_kg": "0",
            "ship_post_fixed_price": None,
            "ship_post_max_weight_kg": None,
            "ship_post_use_json": False,
            "ship_post_json": "",
            "ship_tipax_fixed_price": None,
            "ship_tipax_use_json": False,
            "ship_tipax_json": "",
            "ship_peyk_fixed_price": None,
            "ship_peyk_delivery_cities": "",
            "ship_peyk_use_json": False,
            "ship_peyk_json": "",
            "theme_hero_slides_json": "[]",
            "theme_hero_use_json": False,
            "storage_driver": "local",
            "sms_otp_provider": "console_sms",
            "sms_payamak_username": "",
            "sms_payamak_password": "",
            "sms_payamak_body_id": "",
            "sms_otp_template": "کد ورود ShopCMS: {code}\nاعتبار: ۲ دقیقه",
            "layout_use_custom_header": False,
            "layout_use_custom_footer": False,
            "layout_header_html": "",
            "layout_footer_html": "",
        }

    def _google_verification_display(self, store: Store) -> str:
        from tenants.services.seo import SeoService

        service = SeoService()
        return service.get_verification_token(store) or service.get_html_filename(store)

    def _group_map(self, store: Store, group: str) -> dict[str, Any]:
        return {
            item.key: item.value
            for item in StoreSetting.objects.filter(store=store, group=group)
        }

    def _save_theme(self, store: Store, data: dict[str, Any]) -> None:
        current = self.theme_service.get_theme_settings(store)
        current["logo"] = _as_str(data.get("theme_logo"))
        current["colors"] = {
            "primary": _as_str(data.get("theme_color_primary"), "#0f766e"),
            "background": _as_str(data.get("theme_color_background"), "#f8fafc"),
            "text": _as_str(data.get("theme_color_text"), "#0f172a"),
        }
        current["trust_badges"] = {
            "enamad": {
                "image": _as_str(data.get("trust_enamad_image")),
                "link": _as_str(data.get("trust_enamad_link")),
            },
            "badge2": {
                "image": _as_str(data.get("trust_badge2_image")),
                "link": _as_str(data.get("trust_badge2_link")),
            },
        }
        slides = _parse_json_array(data.get("theme_hero_slides_json"))
        if slides is not None or _as_bool(data.get("theme_hero_use_json")):
            hero = current.get("hero") if isinstance(current.get("hero"), dict) else {}
            current["hero"] = {**hero, "slides": slides or []}
        self.theme_service.update_theme_settings(store, normalize_theme_config(current))

    def _save_contact(self, store: Store, data: dict[str, Any]) -> None:
        mapping = {
            "phone": data.get("contact_phone"),
            "email": data.get("contact_email"),
            "address": data.get("contact_address"),
            "whatsapp": data.get("contact_whatsapp"),
            "instagram": data.get("social_instagram"),
            "telegram": data.get("social_telegram"),
            "twitter": data.get("social_twitter"),
            "linkedin": data.get("social_linkedin"),
            "youtube": data.get("social_youtube"),
        }
        for key, value in mapping.items():
            _set_setting(
                store,
                CONTACT_GROUP,
                key,
                _as_str(value),
                description="اطلاعات تماس و شبکه‌های اجتماعی",
            )

    def _save_seo(self, store: Store, data: dict[str, Any]) -> None:
        mapping = {
            "meta_title": data.get("seo_meta_title"),
            "meta_description": data.get("seo_meta_description"),
            "meta_keywords": data.get("seo_meta_keywords"),
            "og_image": data.get("seo_og_image"),
            "robots": data.get("seo_robots") or "index,follow",
            "canonical_url": data.get("seo_canonical_url"),
        }
        for key, value in mapping.items():
            _set_setting(
                store,
                SEO_GROUP,
                key,
                _as_str(value),
                description="تنظیمات سئو فروشگاه",
            )
        from tenants.services.seo import SeoService

        SeoService().save_google_verification(store, _as_str(data.get("seo_google_site_verification")))

    def _save_tax(self, store: Store, data: dict[str, Any]) -> None:
        _set_setting(
            store,
            TAX_GROUP,
            "on_shipping",
            _as_bool(data.get("tax_on_shipping")),
            description="اعمال مالیات روی هزینه ارسال",
        )
        from taxes.services.tax import TaxService

        TaxService().sync_plugin(store)

    def _save_payment(self, store: Store, data: dict[str, Any]) -> None:
        gateways = data.get("payment_gateways") or []
        if isinstance(gateways, str):
            gateways = [gateways]
        gateways = [str(g) for g in gateways]

        current = self._group_map(store, PAYMENT_GROUP)
        zarinpal = current.get("zarinpal") if isinstance(current.get("zarinpal"), dict) else {}
        zarinpal = {
            **zarinpal,
            "merchant_id": _as_str(data.get("zarinpal_merchant_id")),
            "sandbox": _as_bool(data.get("zarinpal_sandbox"), True),
            "api_base": _as_str(data.get("zarinpal_api_base")),
            "start_pay_url": _as_str(data.get("zarinpal_start_pay_url")),
            "graphql_url": _as_str(data.get("zarinpal_graphql_url")),
        }

        idpay = self._resolve_section_dict(
            data,
            use_json_key="idpay_use_json",
            json_key="idpay_json",
            current=current.get("idpay"),
            form_builder=lambda: {
                "api_key": _as_str(data.get("idpay_api_key")),
                "sandbox": _as_bool(data.get("idpay_sandbox"), True),
            },
        )
        mellat = self._resolve_section_dict(
            data,
            use_json_key="mellat_use_json",
            json_key="mellat_json",
            current=current.get("mellat"),
            form_builder=lambda: {
                "terminal_id": _as_str(data.get("mellat_terminal_id")),
                "username": _as_str(data.get("mellat_username")),
                "password": _as_str(data.get("mellat_password")),
                "sandbox": _as_bool(data.get("mellat_sandbox"), True),
            },
        )
        pasargad = self._resolve_section_dict(
            data,
            use_json_key="pasargad_use_json",
            json_key="pasargad_json",
            current=current.get("pasargad"),
            form_builder=lambda: {
                "merchant_code": _as_str(data.get("pasargad_merchant_code")),
                "terminal_id": _as_str(data.get("pasargad_terminal_id")),
                "sandbox": _as_bool(data.get("pasargad_sandbox"), True),
            },
        )
        sina = self._resolve_section_dict(
            data,
            use_json_key="sina_use_json",
            json_key="sina_json",
            current=current.get("sina"),
            form_builder=lambda: {
                "terminal_id": _as_str(data.get("sina_terminal_id")),
                "sandbox": _as_bool(data.get("sina_sandbox"), True),
            },
        )

        _set_setting(store, PAYMENT_GROUP, "gateways", gateways, description="درگاه‌های فعال")
        _set_setting(
            store,
            PAYMENT_GROUP,
            "default_gateway",
            _as_str(data.get("payment_default_gateway")),
            description="درگاه پیش‌فرض",
        )
        _set_setting(
            store,
            PAYMENT_GROUP,
            "callback_base_url",
            _as_str(data.get("payment_callback_base_url")).rstrip("/"),
            description="آدرس پایه بازگشت پرداخت",
        )
        _set_setting(store, PAYMENT_GROUP, "zarinpal", zarinpal, description="تنظیمات زرین‌پال")
        _set_setting(store, PAYMENT_GROUP, "idpay", idpay, description="تنظیمات آیدی‌پی")
        _set_setting(store, PAYMENT_GROUP, "mellat", mellat, description="تنظیمات ملت")
        _set_setting(store, PAYMENT_GROUP, "pasargad", pasargad, description="تنظیمات پاسارگاد")
        _set_setting(store, PAYMENT_GROUP, "sina", sina, description="تنظیمات سینا")

    def _resolve_section_dict(
        self,
        data: dict[str, Any],
        *,
        use_json_key: str,
        json_key: str,
        current: Any,
        form_builder,
    ) -> dict[str, Any]:
        base = current if isinstance(current, dict) else {}
        parsed = _parse_json_object(data.get(json_key))
        # JSON textarea is always posted with the current value. Apply it when the
        # admin edited that box (or explicitly toggled «ذخیره از JSON»).
        if parsed is not None and (
            _as_bool(data.get(use_json_key)) or not _json_equivalent(parsed, base)
        ):
            return parsed
        built = form_builder()
        return {**base, **built}

    def _save_shipping(self, store: Store, data: dict[str, Any]) -> None:
        current = self._group_map(store, SHIPPING_GROUP)
        origin = current.get("origin") if isinstance(current.get("origin"), dict) else {}
        threshold = _as_decimal_str(data.get("shipping_free_threshold"), "0")
        package_weight = _as_decimal_str(data.get("shipping_base_package_weight_kg"), "0")
        try:
            threshold_decimal = Decimal(threshold)
            threshold_value: Any = (
                int(threshold_decimal)
                if threshold_decimal == threshold_decimal.to_integral_value()
                else float(threshold_decimal)
            )
        except (InvalidOperation, TypeError, ValueError):
            threshold_value = 0

        try:
            package_decimal = Decimal(package_weight)
            package_value: Any = (
                int(package_decimal)
                if package_decimal == package_decimal.to_integral_value()
                else float(package_decimal)
            )
        except (InvalidOperation, TypeError, ValueError):
            package_value = 0

        providers = data.get("shipping_providers") or []
        if isinstance(providers, str):
            providers = [providers]
        providers = [str(p) for p in providers]

        origin = {
            **origin,
            "origin_city": _as_str(data.get("shipping_origin_city"), "مشهد"),
            "origin_province": _as_str(data.get("shipping_origin_province"), "خراسان رضوی"),
            "free_shipping_threshold": threshold_value,
            "base_package_weight_kg": package_value,
        }

        ship_post = self._resolve_section_dict(
            data,
            use_json_key="ship_post_use_json",
            json_key="ship_post_json",
            current=current.get("post"),
            form_builder=lambda: {
                "mode": "fixed",
                "fixed_price": _as_number(data.get("ship_post_fixed_price"), as_int=True),
                "max_weight_kg": _as_number(data.get("ship_post_max_weight_kg")),
            },
        )
        ship_tipax = self._resolve_section_dict(
            data,
            use_json_key="ship_tipax_use_json",
            json_key="ship_tipax_json",
            current=current.get("tipax"),
            form_builder=lambda: {
                "mode": "fixed",
                "fixed_price": _as_number(data.get("ship_tipax_fixed_price"), as_int=True),
            },
        )
        ship_peyk = self._resolve_section_dict(
            data,
            use_json_key="ship_peyk_use_json",
            json_key="ship_peyk_json",
            current=current.get("peyk"),
            form_builder=lambda: {
                "fixed_price": _as_number(data.get("ship_peyk_fixed_price"), as_int=True),
                "delivery_cities": _cities_from_csv(data.get("ship_peyk_delivery_cities")),
            },
        )

        _set_setting(store, SHIPPING_GROUP, "origin", origin, description="مبدا ارسال")
        _set_setting(
            store,
            SHIPPING_GROUP,
            "free_shipping_threshold",
            threshold_value,
            description="آستانه ارسال رایگان",
        )
        _set_setting(
            store,
            SHIPPING_GROUP,
            "providers",
            providers,
            description="ارائه‌دهندگان فعال ارسال",
        )
        _set_setting(
            store,
            SHIPPING_GROUP,
            "default_provider",
            _as_str(data.get("shipping_default_provider")),
            description="ارائه‌دهنده پیش‌فرض ارسال",
        )
        _set_setting(
            store,
            SHIPPING_GROUP,
            "base_package_weight_kg",
            package_value,
            description="وزن بسته‌بندی (کیلوگرم)",
        )
        _set_setting(store, SHIPPING_GROUP, "post", ship_post, description="اسنیپت پست")
        _set_setting(store, SHIPPING_GROUP, "tipax", ship_tipax, description="اسنیپت تیپاکس")
        _set_setting(store, SHIPPING_GROUP, "peyk", ship_peyk, description="اسنیپت پیک")

    def _save_storage(self, store: Store, data: dict[str, Any]) -> None:
        _set_setting(
            store,
            STORAGE_GROUP,
            "driver",
            _as_str(data.get("storage_driver"), "local") or "local",
            description="درایور ذخیره‌سازی رسانه",
        )

    def _save_sms(self, store: Store, data: dict[str, Any]) -> None:
        from notifications.enums import ChannelType
        from notifications.models import NotificationChannel

        current = self._group_map(store, NOTIFICATIONS_GROUP)
        existing = current.get("sms") if isinstance(current.get("sms"), dict) else {}
        provider = _as_str(data.get("sms_otp_provider"), "console_sms") or "console_sms"
        if provider not in {"console_sms", "payamak"}:
            provider = "console_sms"
        password = _as_str(data.get("sms_payamak_password")) or _as_str(existing.get("password"))
        otp_template = _as_str(data.get("sms_otp_template")) or "کد ورود ShopCMS: {code}\nاعتبار: ۲ دقیقه"
        payload = {
            "provider": provider,
            "username": _as_str(data.get("sms_payamak_username")),
            "password": password,
            "body_id": _as_str(data.get("sms_payamak_body_id")),
            "otp_template": otp_template,
        }
        _set_setting(store, NOTIFICATIONS_GROUP, "sms", payload, description="تنظیمات پیامک OTP")

        channel_config = {
            "username": payload["username"],
            "password": payload["password"],
            "body_id": payload["body_id"],
            "otp_template": payload["otp_template"],
        }
        NotificationChannel.objects.filter(store=store, channel_type=ChannelType.SMS).update(is_default=False)
        NotificationChannel.objects.update_or_create(
            store=store,
            channel_type=ChannelType.SMS,
            provider=provider,
            defaults={
                "config": channel_config,
                "is_default": True,
                "is_active": True,
            },
        )

    def _save_layout(self, store: Store, data: dict[str, Any]) -> None:
        header_html = data.get("layout_header_html") or ""
        footer_html = data.get("layout_footer_html") or ""
        use_custom_header = _as_bool(data.get("layout_use_custom_header"))
        use_custom_footer = _as_bool(data.get("layout_use_custom_footer"))
        # Custom chrome with empty HTML hides the theme header/footer — fall back.
        if use_custom_header and not str(header_html).strip():
            use_custom_header = False
        if use_custom_footer and not str(footer_html).strip():
            use_custom_footer = False
        LayoutSettings.objects.update_or_create(
            store=store,
            defaults={
                "use_custom_header": use_custom_header,
                "use_custom_footer": use_custom_footer,
                "header_html": header_html,
                "footer_html": footer_html,
            },
        )
