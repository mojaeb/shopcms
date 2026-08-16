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
            "shipping_origin_city": "تهران",
            "shipping_origin_province": "تهران",
            "shipping_free_threshold": "500000",
            "shipping_default_provider": "post",
            "storage_driver": "local",
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
    assert initial["shipping_origin_city"] == "تهران"
    assert initial["shipping_free_threshold"] == "500000"
    assert initial["layout_use_custom_header"] is True
    assert initial["layout_header_html"] == "<header>hi</header>"

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
        "shipping_free_threshold": "0",
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
        "فروش و مالی",
        "ارسال",
        "سئو و متا",
        "چیدمان و سایر",
        "مدیر فروشگاه",
    ]
    for _title, opts in fieldsets:
        assert "tab" in opts.get("classes", [])
    assert admin.form is StoreConfigForm
    assert {i.model.__name__ for i in admin.inlines} == {"Domain", "StorePlugin", "StoreSetting"}
    assert all(getattr(i, "tab", False) for i in admin.inlines)
    domain_inline = next(i for i in admin.inlines if i.model.__name__ == "Domain")
    assert domain_inline.extra == 0


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
