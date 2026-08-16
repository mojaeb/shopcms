"""Structured store configuration helpers for Unfold admin."""

from __future__ import annotations

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
        (PAYMENT_GROUP, "zarinpal"),
        (SHIPPING_GROUP, "origin"),
        (SHIPPING_GROUP, "free_shipping_threshold"),
        (SHIPPING_GROUP, "default_provider"),
        (STORAGE_GROUP, "driver"),
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
        gateways = payment.get("gateways") or []
        if not isinstance(gateways, list):
            gateways = []

        shipping = self._group_map(store, SHIPPING_GROUP)
        origin = shipping.get("origin") if isinstance(shipping.get("origin"), dict) else {}
        threshold = shipping.get("free_shipping_threshold")
        if threshold is None:
            threshold = origin.get("free_shipping_threshold", 0)

        layout = LayoutSettings.objects.filter(store=store).first()

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
            "zarinpal_merchant_id": _as_str(zarinpal.get("merchant_id")),
            "zarinpal_sandbox": _as_bool(zarinpal.get("sandbox"), True),
            "shipping_origin_city": _as_str(origin.get("origin_city"), "مشهد"),
            "shipping_origin_province": _as_str(origin.get("origin_province"), "خراسان رضوی"),
            "shipping_free_threshold": _as_decimal_str(threshold, "0"),
            "shipping_default_provider": _as_str(shipping.get("default_provider")),
            "storage_driver": _as_str(_get_setting(store, STORAGE_GROUP, "driver", "local"), "local"),
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
            "zarinpal_merchant_id": "",
            "zarinpal_sandbox": True,
            "shipping_origin_city": "مشهد",
            "shipping_origin_province": "خراسان رضوی",
            "shipping_free_threshold": "0",
            "shipping_default_provider": "",
            "storage_driver": "local",
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
        }

        _set_setting(store, PAYMENT_GROUP, "gateways", gateways, description="درگاه‌های فعال")
        _set_setting(
            store,
            PAYMENT_GROUP,
            "default_gateway",
            _as_str(data.get("payment_default_gateway")),
            description="درگاه پیش‌فرض",
        )
        _set_setting(store, PAYMENT_GROUP, "zarinpal", zarinpal, description="تنظیمات زرین‌پال")

    def _save_shipping(self, store: Store, data: dict[str, Any]) -> None:
        current = self._group_map(store, SHIPPING_GROUP)
        origin = current.get("origin") if isinstance(current.get("origin"), dict) else {}
        threshold = _as_decimal_str(data.get("shipping_free_threshold"), "0")
        try:
            threshold_decimal = Decimal(threshold)
            threshold_value: Any = (
                int(threshold_decimal)
                if threshold_decimal == threshold_decimal.to_integral_value()
                else float(threshold_decimal)
            )
        except (InvalidOperation, TypeError, ValueError):
            threshold_value = 0

        origin = {
            **origin,
            "origin_city": _as_str(data.get("shipping_origin_city"), "مشهد"),
            "origin_province": _as_str(data.get("shipping_origin_province"), "خراسان رضوی"),
            "free_shipping_threshold": threshold_value,
        }
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
            "default_provider",
            _as_str(data.get("shipping_default_provider")),
            description="ارائه‌دهنده پیش‌فرض ارسال",
        )

    def _save_storage(self, store: Store, data: dict[str, Any]) -> None:
        _set_setting(
            store,
            STORAGE_GROUP,
            "driver",
            _as_str(data.get("storage_driver"), "local") or "local",
            description="درایور ذخیره‌سازی رسانه",
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
