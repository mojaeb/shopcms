"""Catalog + helpers for StoreSetting rows shown in the advanced JSON admin tab.

Structured form fields (including gateways/shipping snippets in «پیشرفته (فرم)»)
stay in StoreConfigForm. This catalog seeds defaults and powers the copyable
snippet library. Existing values are never overwritten by ensure_*.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from tenants.models import Store, StoreSetting
from tenants.services.theme_settings import DEFAULT_THEME_CONFIG, SAMPLE_HERO_SLIDE

# (group, key, default_value, persian description)
ADVANCED_SETTING_TEMPLATES: tuple[tuple[str, str, Any, str], ...] = (
    (
        "theme",
        "config",
        DEFAULT_THEME_CONFIG,
        "تم فروشگاه: logo، colors، hero.slides[]، trust_badges. "
        "هر اسلاید: image, thumbnail, title, text, button_text, button_link, background_color",
    ),
    (
        "payment",
        "idpay",
        {"api_key": "", "sandbox": True},
        "آیدی‌پی — api_key و sandbox",
    ),
    (
        "payment",
        "mellat",
        {"terminal_id": "", "username": "", "password": "", "sandbox": True},
        "ملت — terminal_id / username / password؛ فعلاً فقط sandbox کامل است",
    ),
    (
        "payment",
        "pasargad",
        {"merchant_code": "", "terminal_id": "", "sandbox": True},
        "پاسارگاد — merchant_code / terminal_id؛ پیاده‌سازی زنده نیازمند گواهی RSA است",
    ),
    (
        "payment",
        "sina",
        {"terminal_id": "", "sandbox": True},
        "سینا — terminal_id؛ فعلاً فقط sandbox",
    ),
    (
        "shipping",
        "post",
        {"mode": "fixed", "fixed_price": 80000, "max_weight_kg": 30},
        "اسنیپت پست (مرجع). روش واقعی را در مدل ShippingMethod بسازید؛ "
        "config روش: fixed_price، max_weight_kg، extra_cost_flat، extra_cost_percent",
    ),
    (
        "shipping",
        "tipax",
        {"mode": "fixed", "fixed_price": 120000},
        "اسنیپت تیپاکس (مرجع). تعرفه شهر/منطقه روی ShippingPrice با zone_tier تنظیم می‌شود",
    ),
    (
        "shipping",
        "peyk",
        {"fixed_price": 40000, "delivery_cities": ["مشهد"]},
        "اسنیپت پیک. delivery_cities خالی = همه شهرها؛ در غیر این صورت فقط همان شهرها",
    ),
)


# Copy-paste library for admins (new stores / editing current). Never auto-applied.
# category: تم | پرداخت | ارسال | روش‌ارسال
COPYABLE_SNIPPETS: tuple[dict[str, Any], ...] = (
    {
        "id": "theme-empty",
        "category": "تم",
        "title": "تم خالی (پایه)",
        "hint": "برای فروشگاه جدید؛ اسلاید ندارد. در تنظیم پیشرفته: theme / config",
        "target": "theme.config",
        "value": DEFAULT_THEME_CONFIG,
    },
    {
        "id": "theme-hero-sample",
        "category": "تم",
        "title": "تم با یک اسلاید نمونه",
        "hint": "hero.slides را کامل می‌کند؛ لوگو و رنگ‌ها قابل ویرایش‌اند",
        "target": "theme.config",
        "value": {
            **deepcopy(DEFAULT_THEME_CONFIG),
            "hero": {"slides": [deepcopy(SAMPLE_HERO_SLIDE)]},
        },
    },
    {
        "id": "theme-hero-two",
        "category": "تم",
        "title": "تم با دو اسلاید",
        "hint": "الگوی چنداسلایده برای کپی و عوض کردن متن/عکس",
        "target": "theme.config",
        "value": {
            **deepcopy(DEFAULT_THEME_CONFIG),
            "hero": {
                "slides": [
                    deepcopy(SAMPLE_HERO_SLIDE),
                    {
                        **deepcopy(SAMPLE_HERO_SLIDE),
                        "title": "پیشنهاد ویژه این هفته",
                        "text": "تخفیف روی منتخب محصولات — فقط تا پایان هفته.",
                        "button_text": "مشاهده پیشنهادها",
                        "button_link": "/products/",
                        "background_color": "#0f172a",
                    },
                ]
            },
        },
    },
    {
        "id": "payment-idpay-sandbox",
        "category": "پرداخت",
        "title": "آیدی‌پی — آزمایشی",
        "hint": "payment / idpay",
        "target": "payment.idpay",
        "value": {"api_key": "sandbox-key", "sandbox": True},
    },
    {
        "id": "payment-idpay-live",
        "category": "پرداخت",
        "title": "آیدی‌پی — زنده (جایگزین کلید)",
        "hint": "api_key واقعی را جایگزین کنید؛ sandbox را false بگذارید",
        "target": "payment.idpay",
        "value": {"api_key": "YOUR_IDPAY_API_KEY", "sandbox": False},
    },
    {
        "id": "payment-mellat-sandbox",
        "category": "پرداخت",
        "title": "ملت — آزمایشی",
        "hint": "payment / mellat — زنده هنوز کامل نیست",
        "target": "payment.mellat",
        "value": {
            "terminal_id": "sandbox-terminal",
            "username": "",
            "password": "",
            "sandbox": True,
        },
    },
    {
        "id": "payment-pasargad-sandbox",
        "category": "پرداخت",
        "title": "پاسارگاد — آزمایشی",
        "hint": "payment / pasargad",
        "target": "payment.pasargad",
        "value": {"merchant_code": "sandbox-pasargad", "terminal_id": "", "sandbox": True},
    },
    {
        "id": "payment-sina-sandbox",
        "category": "پرداخت",
        "title": "سینا — آزمایشی",
        "hint": "payment / sina",
        "target": "payment.sina",
        "value": {"terminal_id": "sandbox-sina", "sandbox": True},
    },
    {
        "id": "payment-zarinpal-ref",
        "category": "پرداخت",
        "title": "زرین‌پال — مرجع (تب فروش و مالی)",
        "hint": "معمولاً از تب فرم ذخیره می‌شود؛ برای کپی به فروشگاه دیگر مفید است. access_token فقط برای بازگشت وجه GraphQL",
        "target": "payment.zarinpal",
        "value": {
            "merchant_id": "sandbox-merchant",
            "sandbox": True,
            "access_token": "",
            "api_base": "",
            "start_pay_url": "",
            "graphql_url": "",
        },
    },
    {
        "id": "payment-zarinpal-live-ref",
        "category": "پرداخت",
        "title": "زرین‌پال — زنده (مرجع)",
        "hint": "merchant_id واقعی UUID؛ در صورت نیاز api_base / start_pay_url / graphql_url را پر کنید",
        "target": "payment.zarinpal",
        "value": {
            "merchant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "sandbox": False,
            "access_token": "",
            "api_base": "https://api.zarinpal.com/pg/v4/payment",
            "start_pay_url": "https://www.zarinpal.com/pg/StartPay/{authority}",
            "graphql_url": "https://next.zarinpal.com/api/v4/graphql",
        },
    },
    {
        "id": "payment-callback-base",
        "category": "پرداخت",
        "title": "آدرس پایه Callback فروشگاه",
        "hint": "payment / callback_base_url — مقدار رشتهٔ URL بدون اسلش پایانی",
        "target": "payment.callback_base_url",
        "value": "https://shop.example.com",
    },
    {
        "id": "payment-zarinpal-custom-urls",
        "category": "پرداخت",
        "title": "زرین‌پال — URLهای سفارشی",
        "hint": "برای پروکسی یا endpoint جایگزین؛ خالی = پیش‌فرض رسمی",
        "target": "payment.zarinpal",
        "value": {
            "merchant_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "sandbox": False,
            "api_base": "https://api.zarinpal.com/pg/v4/payment",
            "start_pay_url": "https://www.zarinpal.com/pg/StartPay/{authority}",
            "graphql_url": "https://next.zarinpal.com/api/v4/graphql",
            "access_token": "",
        },
    },
    {
        "id": "shipping-post-snippet",
        "category": "ارسال",
        "title": "اسنیپت پست (StoreSetting)",
        "hint": "shipping / post — مرجع؛ روش واقعی در ShippingMethod",
        "target": "shipping.post",
        "value": {"mode": "fixed", "fixed_price": 80000, "max_weight_kg": 30},
    },
    {
        "id": "shipping-tipax-snippet",
        "category": "ارسال",
        "title": "اسنیپت تیپاکس (StoreSetting)",
        "hint": "shipping / tipax",
        "target": "shipping.tipax",
        "value": {"mode": "fixed", "fixed_price": 120000},
    },
    {
        "id": "shipping-peyk-snippet",
        "category": "ارسال",
        "title": "اسنیپت پیک — محدود به شهر",
        "hint": "shipping / peyk — delivery_cities خالی = همه شهرها",
        "target": "shipping.peyk",
        "value": {"fixed_price": 40000, "delivery_cities": ["مشهد", "تهران"]},
    },
    {
        "id": "shipping-origin-ref",
        "category": "ارسال",
        "title": "مبدا ارسال (مرجع — تب ارسال)",
        "hint": "معمولاً از تب فرم؛ برای کپی بین فروشگاه‌ها",
        "target": "shipping.origin",
        "value": {
            "origin_city": "مشهد",
            "origin_province": "خراسان رضوی",
            "free_shipping_threshold": 0,
            "base_package_weight_kg": 0.1,
        },
    },
    {
        "id": "method-post-fixed",
        "category": "روش‌ارسال",
        "title": "ShippingMethod.config — پست ثابت + سقف وزن",
        "hint": "در ادمین روش ارسال، فیلد config را با این JSON جایگزین کنید",
        "target": "ShippingMethod.config",
        "value": {
            "fixed_price": 80000,
            "origin_city": "مشهد",
            "max_weight_kg": 30,
        },
    },
    {
        "id": "method-post-extra",
        "category": "روش‌ارسال",
        "title": "پست با هزینه اضافه (ثابت + درصد)",
        "hint": "extra_cost_flat و extra_cost_percent روی قیمت پایه اعمال می‌شود",
        "target": "ShippingMethod.config",
        "value": {
            "fixed_price": 100000,
            "extra_cost_flat": 5000,
            "extra_cost_percent": 10,
            "max_weight_kg": 30,
        },
    },
    {
        "id": "method-tipax-distance",
        "category": "روش‌ارسال",
        "title": "تیپاکس مسافتی (fallback قیمت)",
        "hint": "تعرفه دقیق را در ShippingPrice بسازید؛ fixed_price پشتیبان است",
        "target": "ShippingMethod.config",
        "value": {"origin_city": "مشهد", "fixed_price": 100000},
    },
    {
        "id": "method-peyk-cities",
        "category": "روش‌ارسال",
        "title": "پیک فقط چند شهر",
        "hint": "اگر شهر مقصد در لیست نباشد، روش در چک‌اوت دیده نمی‌شود",
        "target": "ShippingMethod.config",
        "value": {
            "fixed_price": 45000,
            "delivery_cities": ["مشهد", "نیشابور", "طرقبه"],
        },
    },
    {
        "id": "method-peyk-all",
        "category": "روش‌ارسال",
        "title": "پیک همه شهرها",
        "hint": "delivery_cities خالی یا حذف‌شده = بدون محدودیت شهر",
        "target": "ShippingMethod.config",
        "value": {"fixed_price": 45000, "delivery_cities": []},
    },
    {
        "id": "price-zone-same",
        "category": "روش‌ارسال",
        "title": "تعرفه منطقه‌ای — هم‌استان",
        "hint": "ردیف ShippingPrice: to_city خالی، zone_tier=same",
        "target": "ShippingPrice (فیلدها)",
        "value": {
            "from_city": "",
            "to_city": "",
            "zone_tier": "same",
            "price": 70000,
            "extra_per_kg": 0,
        },
    },
    {
        "id": "price-zone-adjacent",
        "category": "روش‌ارسال",
        "title": "تعرفه منطقه‌ای — استان مجاور",
        "hint": "zone_tier=adjacent",
        "target": "ShippingPrice (فیلدها)",
        "value": {
            "from_city": "",
            "to_city": "",
            "zone_tier": "adjacent",
            "price": 110000,
            "extra_per_kg": 0,
        },
    },
    {
        "id": "price-zone-far",
        "category": "روش‌ارسال",
        "title": "تعرفه منطقه‌ای — دورافتاده",
        "hint": "zone_tier=far",
        "target": "ShippingPrice (فیلدها)",
        "value": {
            "from_city": "",
            "to_city": "",
            "zone_tier": "far",
            "price": 180000,
            "extra_per_kg": 0,
        },
    },
    {
        "id": "price-city-pair",
        "category": "روش‌ارسال",
        "title": "تعرفه شهر به شهر (اولویت بالاتر از منطقه)",
        "hint": "اگر این ردیف match شود، zone_tier نادیده گرفته می‌شود",
        "target": "ShippingPrice (فیلدها)",
        "value": {
            "from_city": "مشهد",
            "to_city": "تهران",
            "zone_tier": "",
            "price": 150000,
            "extra_per_kg": 5000,
        },
    },
)


def advanced_setting_description(group: str, key: str) -> str:
    for g, k, _default, description in ADVANCED_SETTING_TEMPLATES:
        if g == group and k == key:
            return description
    return ""


def advanced_setting_default(group: str, key: str) -> Any | None:
    for g, k, default, _description in ADVANCED_SETTING_TEMPLATES:
        if g == group and k == key:
            return deepcopy(default)
    return None


def ensure_advanced_setting_rows(store: Store) -> int:
    """Create missing advanced JSON rows with templates. Never overwrite existing values."""
    created = 0
    for group, key, default, description in ADVANCED_SETTING_TEMPLATES:
        _, was_created = StoreSetting.objects.get_or_create(
            store=store,
            group=group,
            key=key,
            defaults={
                "value": deepcopy(default),
                "value_type": "json",
                "description": description,
            },
        )
        if was_created:
            created += 1
            continue
        # Fill blank description on existing rows so the admin always shows guidance.
        row = StoreSetting.objects.filter(store=store, group=group, key=key).first()
        if row and not (row.description or "").strip() and description:
            row.description = description
            row.save(update_fields=["description", "updated_at"])
    return created


def list_copyable_snippets() -> list[dict[str, Any]]:
    """Serialize snippet library for the admin docs hub (pretty JSON + metadata)."""
    items: list[dict[str, Any]] = []
    for raw in COPYABLE_SNIPPETS:
        value = deepcopy(raw["value"])
        items.append(
            {
                "id": raw["id"],
                "category": raw["category"],
                "title": raw["title"],
                "hint": raw["hint"],
                "target": raw["target"],
                "json": json.dumps(value, ensure_ascii=False, indent=2),
            }
        )
    return items


def copyable_snippet_categories(snippets: list[dict[str, Any]] | None = None) -> list[str]:
    items = snippets if snippets is not None else list_copyable_snippets()
    seen: list[str] = []
    for item in items:
        cat = item["category"]
        if cat not in seen:
            seen.append(cat)
    return seen
