"""Tests for unified store config admin form/service."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from accounts.models import User
from cms.models import LayoutSettings
from tenants.admin import StoreAdmin
from tenants.forms import StoreConfigForm
from tenants.models import Store, StoreSetting, Theme
from tenants.services.store_config import StoreConfigService
from tenants.services.theme_settings import ThemeSettingsService


@pytest.fixture
def theme(db):
    return Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)


@pytest.fixture
def store(db, theme):
    return Store.objects.create(
        name="فروشگاه تست",
        slug="config-shop",
        theme=theme,
        default_theme=theme,
        currency="IRR",
        status="active",
        tax_enabled=True,
        tax_percent=9,
    )


@pytest.mark.django_db
def test_store_config_service_roundtrip(store):
    service = StoreConfigService()
    service.save_admin_data(
        store,
        {
            "theme_logo": "https://cdn.example/logo.png",
            "theme_color_primary": "#112233",
            "theme_color_background": "#fafafa",
            "theme_color_text": "#111111",
            "trust_enamad_image": "https://cdn.example/enamad.png",
            "trust_enamad_link": "https://trustseal.enamad.ir/x",
            "trust_badge2_image": "",
            "trust_badge2_link": "",
            "contact_phone": "02191000000",
            "contact_email": "shop@example.com",
            "contact_address": "تهران",
            "contact_whatsapp": "09120000000",
            "social_instagram": "https://instagram.com/shop",
            "social_telegram": "https://t.me/shop",
            "social_twitter": "",
            "social_linkedin": "",
            "social_youtube": "",
            "seo_meta_title": "عنوان فروشگاه",
            "seo_meta_description": "توضیح",
            "seo_meta_keywords": "فروشگاه,تست",
            "seo_og_image": "https://cdn.example/og.jpg",
            "seo_robots": "index,follow",
            "seo_canonical_url": "https://shop.example/",
            "seo_google_site_verification": "GscToken_storecfg1",
            "tax_on_shipping": True,
            "payment_default_gateway": "zarinpal",
            "payment_gateways": ["zarinpal", "idpay"],
            "zarinpal_merchant_id": "merchant-1",
            "zarinpal_sandbox": True,
            "payment_callback_base_url": "https://shop.example.com",
            "zarinpal_api_base": "https://api.zarinpal.com/pg/v4/payment",
            "zarinpal_start_pay_url": "https://www.zarinpal.com/pg/StartPay/{authority}",
            "zarinpal_graphql_url": "",
            "shipping_origin_city": "تهران",
            "shipping_origin_province": "تهران",
            "shipping_providers": ["post", "tipax"],
            "shipping_free_threshold": "500000",
            "shipping_default_provider": "post",
            "shipping_base_package_weight_kg": "0.100",
            "storage_driver": "local",
            "sms_otp_provider": "payamak",
            "sms_payamak_username": "user1",
            "sms_payamak_password": "secret",
            "sms_payamak_body_id": "226930",
            "sms_otp_template": "کد ورود: {code}",
            "layout_use_custom_header": True,
            "layout_use_custom_footer": False,
            "layout_header_html": "<header>hi</header>",
            "layout_footer_html": "",
        },
    )

    initial = service.get_admin_initial(store)
    assert initial["theme_logo"] == "https://cdn.example/logo.png"
    assert initial["theme_color_primary"] == "#112233"
    assert initial["contact_phone"] == "02191000000"
    assert initial["social_instagram"] == "https://instagram.com/shop"
    assert initial["seo_meta_title"] == "عنوان فروشگاه"
    assert initial["seo_google_site_verification"] == "GscToken_storecfg1"
    assert initial["tax_on_shipping"] is True
    assert initial["payment_gateways"] == ["zarinpal", "idpay"]
    assert initial["zarinpal_merchant_id"] == "merchant-1"
    assert initial["payment_callback_base_url"] == "https://shop.example.com"
    assert initial["zarinpal_api_base"] == "https://api.zarinpal.com/pg/v4/payment"
    assert initial["shipping_origin_city"] == "تهران"
    assert initial["shipping_free_threshold"] == "500000"
    assert initial["shipping_providers"] == ["post", "tipax"]
    assert initial["shipping_base_package_weight_kg"] == "0.1"
    assert initial["layout_use_custom_header"] is True
    assert initial["layout_header_html"] == "<header>hi</header>"
    assert initial["sms_otp_provider"] == "payamak"
    assert initial["sms_payamak_username"] == "user1"
    assert initial["sms_payamak_body_id"] == "226930"
    assert initial["sms_payamak_password"] == ""

    from notifications.models import NotificationChannel

    channel = NotificationChannel.objects.get(store=store, provider="payamak")
    assert channel.is_default is True
    assert channel.config["body_id"] == "226930"
    assert channel.config["password"] == "secret"

    theme = ThemeSettingsService().get_theme_settings(store)
    assert theme["logo"] == "https://cdn.example/logo.png"
    assert theme["trust_badges"]["enamad"]["link"] == "https://trustseal.enamad.ir/x"

    assert StoreSetting.objects.filter(store=store, group="contact", key="phone").exists()
    assert StoreSetting.objects.filter(store=store, group="seo", key="meta_title").exists()
    assert StoreSetting.objects.get(store=store, group="seo", key="google_site_verification").value == (
        "GscToken_storecfg1"
    )
    layout = LayoutSettings.objects.get(store=store)
    assert layout.use_custom_header is True


@pytest.mark.django_db
def test_sms_password_preserved_when_blank_on_resave(store):
    service = StoreConfigService()
    service.save_admin_data(
        store,
        {
            **service.get_admin_initial(store),
            "sms_otp_provider": "payamak",
            "sms_payamak_username": "user1",
            "sms_payamak_password": "secret",
            "sms_payamak_body_id": "226930",
        },
    )
    service.save_admin_data(
        store,
        {
            **service.get_admin_initial(store),
            "sms_otp_provider": "payamak",
            "sms_payamak_username": "user1",
            "sms_payamak_password": "",
            "sms_payamak_body_id": "226930",
        },
    )
    from notifications.models import NotificationChannel

    channel = NotificationChannel.objects.get(store=store, provider="payamak")
    assert channel.config["password"] == "secret"


@pytest.mark.django_db
def test_store_config_ignores_empty_custom_layout_html(store):
    StoreConfigService().save_admin_data(
        store,
        {
            **StoreConfigService().get_admin_initial(store),
            "layout_use_custom_header": True,
            "layout_use_custom_footer": True,
            "layout_header_html": "   ",
            "layout_footer_html": "",
        },
    )
    layout = LayoutSettings.objects.get(store=store)
    assert layout.use_custom_header is False
    assert layout.use_custom_footer is False


@pytest.mark.django_db
def test_store_config_preserves_hero_slides(store):
    ThemeSettingsService().update_theme_settings(
        store,
        {
            "logo": "",
            "colors": {"primary": "#0f766e", "background": "#f8fafc", "text": "#0f172a"},
            "hero": {
                "slides": [
                    {
                        "image": "https://cdn.example/hero.jpg",
                        "title": "اسلاید",
                        "text": "متن",
                        "button_text": "خرید",
                        "button_link": "/products/",
                        "background_color": "#eee",
                        "thumbnail": "",
                    }
                ]
            },
            "trust_badges": {"enamad": {"image": "", "link": ""}, "badge2": {"image": "", "link": ""}},
        },
    )
    StoreConfigService().save_admin_data(
        store,
        {
            **StoreConfigService().get_admin_initial(store),
            "theme_logo": "https://cdn.example/new-logo.png",
            "theme_color_primary": "#abcdef",
        },
    )
    theme = ThemeSettingsService().get_theme_settings(store)
    assert theme["logo"] == "https://cdn.example/new-logo.png"
    assert theme["colors"]["primary"] == "#abcdef"
    assert len(theme["hero"]["slides"]) == 1
    assert theme["hero"]["slides"][0]["title"] == "اسلاید"


@pytest.mark.django_db
def test_store_config_form_initial_and_save(store):
    StoreSetting.objects.create(
        store=store,
        group="contact",
        key="phone",
        value="02111111111",
    )
    form = StoreConfigForm(instance=store)
    assert form.fields["contact_phone"].initial == "02111111111"

    payload = {
        "name": store.name,
        "slug": store.slug,
        "store_type": store.store_type,
        "status": store.status,
        "theme": store.theme_id,
        "default_theme": store.default_theme_id,
        "currency": "IRR",
        "timezone": "Asia/Tehran",
        "language": "fa",
        "tax_enabled": True,
        "tax_percent": "9",
        "contact_phone": "02122222222",
        "contact_email": "a@b.com",
        "seo_meta_title": "SEO Title",
        "payment_gateways": ["zarinpal"],
        "payment_default_gateway": "zarinpal",
        "zarinpal_sandbox": True,
        "shipping_origin_city": "مشهد",
        "shipping_origin_province": "خراسان رضوی",
        "shipping_providers": ["post"],
        "shipping_free_threshold": "0",
        "shipping_default_provider": "post",
        "shipping_base_package_weight_kg": "0.1",
        "storage_driver": "local",
        "seo_robots": "index,follow",
        "theme_color_primary": "#0f766e",
        "theme_color_background": "#f8fafc",
        "theme_color_text": "#0f172a",
    }
    form = StoreConfigForm(payload, instance=store)
    assert form.is_valid(), form.errors
    form.save()
    form.save_related_config()
    assert StoreSetting.objects.get(store=store, group="contact", key="phone").value == "02122222222"
    assert StoreSetting.objects.get(store=store, group="seo", key="meta_title").value == "SEO Title"
    assert StoreSetting.objects.get(store=store, group="shipping", key="base_package_weight_kg").value == 0.1
    assert StoreSetting.objects.get(store=store, group="shipping", key="providers").value == ["post"]
    assert StoreSetting.objects.get(store=store, group="shipping", key="default_provider").value == "post"


@pytest.mark.django_db
def test_store_admin_fieldsets_use_persian_tabs(store):
    site = AdminSite()
    admin = StoreAdmin(Store, site)
    request = RequestFactory().get("/")
    request.user = User.objects.create_superuser(phone="09120001111", password="x")
    fieldsets = admin.get_fieldsets(request, store)
    titles = [fs[0] for fs in fieldsets]
    assert titles == [
        "اطلاعات پایه",
        "دامنه و برندینگ",
        "تماس و شبکه‌های اجتماعی",
        "پیامک OTP",
        "فروش و مالی",
        "ارسال",
        "سئو و متا",
        "چیدمان و سایر",
        "پیشرفته (فرم)",
        "مدیر فروشگاه",
    ]
    for _title, opts in fieldsets:
        assert "tab" in opts.get("classes", [])
    assert admin.form is StoreConfigForm
    assert {i.model.__name__ for i in admin.inlines} == {
        "Domain",
        "ShippingMethod",
        "StorePlugin",
        "StoreSetting",
    }
    assert all(getattr(i, "tab", False) for i in admin.inlines)
    domain_inline = next(i for i in admin.inlines if i.model.__name__ == "Domain")
    assert domain_inline.extra == 0
    shipping_inline = next(i for i in admin.inlines if i.model.__name__ == "ShippingMethod")
    assert shipping_inline.extra == 0
    assert shipping_inline.show_change_link is True


@pytest.mark.django_db
def test_store_setting_inline_hides_structured_keys_and_allows_empty_json(store):
    """Empty-string JSON values must not block admin save; structured keys stay out of inline."""
    from tenants.admin import StoreSettingInline, _StoreSettingInlineForm

    StoreSetting.objects.create(store=store, group="contact", key="phone", value="")
    StoreSetting.objects.create(
        store=store,
        group="theme",
        key="config",
        value={"logo": "", "hero": {"slides": []}, "colors": {}},
    )
    StoreSetting.objects.create(store=store, group="custom", key="flag", value="")

    site = AdminSite()
    inline = StoreSettingInline(Store, site)
    request = RequestFactory().get("/")
    request.user = User.objects.create_superuser(phone="09120002222", password="x")
    qs = inline.get_queryset(request).filter(store=store)
    keys = {(row.group, row.key) for row in qs}
    assert ("contact", "phone") not in keys
    assert ("payment", "idpay") not in keys
    assert ("shipping", "peyk") not in keys
    assert ("theme", "config") in keys
    assert ("custom", "flag") in keys

    form = _StoreSettingInlineForm(
        data={
            "group": "custom",
            "key": "flag",
            "value": '""',
            "value_type": "json",
            "description": "",
        },
        instance=StoreSetting.objects.get(store=store, group="custom", key="flag"),
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["value"] == ""


@pytest.mark.django_db
def test_pretty_json_form_indents_value(store):
    from tenants.admin import PrettyJSONFormField, _StoreSettingInlineForm

    setting = StoreSetting.objects.create(
        store=store,
        group="payment",
        key="idpay",
        value={"api_key": "x", "sandbox": True},
    )
    form = _StoreSettingInlineForm(instance=setting)
    prepared = form.fields["value"].prepare_value(setting.value)
    assert '"api_key": "x"' in prepared
    assert "\n" in prepared

    field = PrettyJSONFormField()
    assert field.prepare_value({"a": 1}).startswith("{")


@pytest.mark.django_db
def test_ensure_advanced_setting_rows_preserves_existing(store):
    from tenants.services.advanced_settings import ensure_advanced_setting_rows

    StoreSetting.objects.create(
        store=store,
        group="theme",
        key="config",
        value={"logo": "https://cdn.example/keep.png", "hero": {"slides": [{"title": "keep"}]}},
        description="",
    )
    created = ensure_advanced_setting_rows(store)
    assert created >= 1
    theme = StoreSetting.objects.get(store=store, group="theme", key="config")
    assert theme.value["logo"] == "https://cdn.example/keep.png"
    assert theme.value["hero"]["slides"][0]["title"] == "keep"
    assert "اسلاید" in theme.description or "hero" in theme.description
    assert StoreSetting.objects.filter(store=store, group="shipping", key="peyk").exists()
    assert StoreSetting.objects.filter(store=store, group="payment", key="sina").exists()
    # Second call must not overwrite or duplicate.
    ensure_advanced_setting_rows(store)
    assert StoreSetting.objects.filter(store=store, group="theme", key="config").count() == 1
    assert StoreSetting.objects.get(store=store, group="theme", key="config").value["logo"] == (
        "https://cdn.example/keep.png"
    )
@pytest.mark.django_db
def test_copyable_snippets_library():
    from tenants.services.advanced_settings import (
        COPYABLE_SNIPPETS,
        copyable_snippet_categories,
        list_copyable_snippets,
    )

    items = list_copyable_snippets()
    assert len(items) == len(COPYABLE_SNIPPETS)
    assert len(items) >= 10
    ids = {i["id"] for i in items}
    assert "theme-hero-sample" in ids
    assert "method-peyk-cities" in ids
    assert "price-zone-adjacent" in ids
    sample = next(i for i in items if i["id"] == "theme-empty")
    assert sample["target"] == "theme.config"
    assert '"logo"' in sample["json"]
    assert "\n" in sample["json"]
    cats = copyable_snippet_categories(items)
    assert "تم" in cats
    assert "پرداخت" in cats
    assert "ارسال" in cats
    assert "روش‌ارسال" in cats


@pytest.mark.django_db
def test_advanced_form_tab_saves_gateways_snippets_and_hero(store):
    service = StoreConfigService()
    base = service.get_admin_initial(store)
    service.save_admin_data(
        store,
        {
            **base,
            "idpay_api_key": "idpay-live-key",
            "idpay_sandbox": False,
            "idpay_use_json": False,
            "mellat_use_json": True,
            "mellat_json": '{"terminal_id": "mellat-1", "username": "u", "password": "p", "sandbox": true}',
            "ship_peyk_fixed_price": 45000,
            "ship_peyk_delivery_cities": "مشهد, تهران",
            "ship_peyk_use_json": False,
            "theme_hero_use_json": True,
            "theme_hero_slides_json": '[{"title": "از فرم", "text": "توضیح", "image": "", "thumbnail": "", "button_text": "برو", "button_link": "/", "background_color": "#111"}]',
        },
    )

    assert StoreSetting.objects.get(store=store, group="payment", key="idpay").value == {
        "api_key": "idpay-live-key",
        "sandbox": False,
    }
    mellat = StoreSetting.objects.get(store=store, group="payment", key="mellat").value
    assert mellat["terminal_id"] == "mellat-1"
    assert mellat["username"] == "u"
    peyk = StoreSetting.objects.get(store=store, group="shipping", key="peyk").value
    assert peyk["fixed_price"] == 45000
    assert peyk["delivery_cities"] == ["مشهد", "تهران"]

    theme = ThemeSettingsService().get_theme_settings(store)
    assert theme["hero"]["slides"][0]["title"] == "از فرم"

    initial = service.get_admin_initial(store)
    assert initial["idpay_api_key"] == "idpay-live-key"
    assert initial["idpay_sandbox"] is False
    assert "mellat-1" in initial["mellat_json"]
    assert "مشهد" in initial["ship_peyk_delivery_cities"]
    assert "از فرم" in initial["theme_hero_slides_json"]


@pytest.mark.django_db
def test_advanced_json_saves_without_use_json_switch(store):
    """Editing JSON textareas must persist even if «ذخیره از JSON» stays off."""
    service = StoreConfigService()
    service.save_admin_data(
        store,
        {
            **service.get_admin_initial(store),
            "idpay_api_key": "old-key",
            "idpay_sandbox": True,
            "ship_peyk_fixed_price": 40000,
            "ship_peyk_delivery_cities": "مشهد",
        },
    )
    initial = service.get_admin_initial(store)
    service.save_admin_data(
        store,
        {
            **initial,
            "idpay_use_json": False,
            "idpay_json": '{"api_key": "pasted-key", "sandbox": false}',
            "ship_peyk_use_json": False,
            "ship_peyk_json": '{"fixed_price": 55000, "delivery_cities": ["تهران"]}',
            "theme_hero_use_json": False,
            "theme_hero_slides_json": '[{"title": "اسلاید جدید", "text": "", "image": "", "thumbnail": "", "button_text": "", "button_link": "", "background_color": "#000"}]',
        },
    )
    assert StoreSetting.objects.get(store=store, group="payment", key="idpay").value == {
        "api_key": "pasted-key",
        "sandbox": False,
    }
    peyk = StoreSetting.objects.get(store=store, group="shipping", key="peyk").value
    assert peyk["fixed_price"] == 55000
    assert peyk["delivery_cities"] == ["تهران"]
    theme = ThemeSettingsService().get_theme_settings(store)
    assert theme["hero"]["slides"][0]["title"] == "اسلاید جدید"


@pytest.mark.django_db
def test_advanced_form_fields_win_when_json_unchanged(store):
    service = StoreConfigService()
    service.save_admin_data(
        store,
        {
            **service.get_admin_initial(store),
            "idpay_api_key": "old-key",
            "idpay_sandbox": True,
        },
    )
    initial = service.get_admin_initial(store)
    service.save_admin_data(
        store,
        {
            **initial,
            "idpay_api_key": "form-key",
            "idpay_sandbox": False,
            "idpay_use_json": False,
            "idpay_json": initial["idpay_json"],
        },
    )
    assert StoreSetting.objects.get(store=store, group="payment", key="idpay").value == {
        "api_key": "form-key",
        "sandbox": False,
    }


@pytest.mark.django_db
def test_store_shipping_method_inline_saves_method(store):
    from tenants.admin import _ShippingMethodInlineForm
    from shipping.models import ShippingMethod

    form = _ShippingMethodInlineForm(
        data={
            "name": "پست پیشتاز",
            "slug": "post-express",
            "provider": "post",
            "calculation_mode": "fixed",
            "payment_type": "prepaid",
            "zone": "",
            "is_active": True,
            "sort_order": "1",
            "estimated_days": "4",
            "min_order_amount": "0",
            "free_shipping_threshold": "",
            "config": '{"fixed_price": 95000, "max_weight_kg": 20}',
        },
    )
    form.instance.store = store
    assert form.is_valid(), form.errors
    method = form.save(commit=False)
    method.store = store
    method.save()
    saved = ShippingMethod.objects.get(store=store, slug="post-express")
    assert saved.name == "پست پیشتاز"
    assert saved.config["fixed_price"] == 95000
    assert saved.config["max_weight_kg"] == 20
