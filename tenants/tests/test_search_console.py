"""Tests for Google Search Console verification, sitemap, and robots.txt."""

import pytest

from cms.models import Page
from products.enums import ProductStatus, ProductType
from products.models import Category, Product
from tenants.models import Domain, Store, StoreSetting, Theme
from tenants.services.seo import SeoError, SeoService, parse_google_verification
from tenants.services.store_config import StoreConfigService


@pytest.fixture
def theme(db):
    return Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)


@pytest.fixture
def store(db, theme):
    store = Store.objects.create(
        name="فروشگاه کنسول",
        slug="gsc-shop",
        theme=theme,
        default_theme=theme,
        status="active",
    )
    Domain.objects.create(store=store, domain="gsc.local", is_primary=True)
    return store


@pytest.mark.parametrize(
    "raw,token,html_file",
    [
        ("", "", ""),
        ("   ", "", ""),
        ("AbCdefghij_12-34", "AbCdefghij_12-34", ""),
        (
            '<meta name="google-site-verification" content="Tok_en-12345678">',
            "Tok_en-12345678",
            "",
        ),
        ("googleXYZ99.html", "", "googlexyz99.html"),
        (
            "google-site-verification: googleFile01.html",
            "",
            "googlefile01.html",
        ),
    ],
)
def test_parse_google_verification(raw, token, html_file):
    assert parse_google_verification(raw) == (token, html_file)


def test_parse_google_verification_rejects_junk():
    with pytest.raises(SeoError):
        parse_google_verification("not a valid code!")


@pytest.mark.django_db
def test_store_config_saves_google_meta_token(store):
    StoreConfigService().save_admin_data(
        store,
        {
            **StoreConfigService().get_admin_initial(store),
            "seo_google_site_verification": (
                '<meta name="google-site-verification" content="MetaToken_abc123">'
            ),
        },
    )
    initial = StoreConfigService().get_admin_initial(store)
    assert initial["seo_google_site_verification"] == "MetaToken_abc123"
    assert StoreSetting.objects.get(
        store=store, group="seo", key="google_site_verification"
    ).value == "MetaToken_abc123"
    assert StoreSetting.objects.get(store=store, group="seo", key="google_html_file").value == ""


@pytest.mark.django_db
def test_homepage_includes_google_meta(client, store):
    SeoService().save_google_verification(store, "HomeToken_xyz98765")
    response = client.get("/", HTTP_HOST="gsc.local")
    assert response.status_code == 200
    html = response.content.decode()
    assert 'name="google-site-verification"' in html
    assert 'content="HomeToken_xyz98765"' in html


@pytest.mark.django_db
def test_robots_and_sitemap(client, store):
    category = Category.objects.create(store=store, name="کالای دیجیتال", slug="digital", is_active=True)
    Product.objects.create(
        store=store,
        category=category,
        name="لپ‌تاپ",
        slug="laptop",
        product_type=ProductType.SIMPLE,
        status=ProductStatus.ACTIVE,
        base_price=1000,
    )
    Product.objects.create(
        store=store,
        name="پیش‌نویس",
        slug="draft-item",
        product_type=ProductType.SIMPLE,
        status=ProductStatus.DRAFT,
        base_price=1,
    )
    Page.objects.create(store=store, title="درباره", slug="about", is_published=True)

    robots = client.get("/robots.txt", HTTP_HOST="gsc.local")
    assert robots.status_code == 200
    assert robots["Content-Type"].startswith("text/plain")
    body = robots.content.decode()
    assert "Sitemap: http://gsc.local/sitemap.xml" in body
    assert "Disallow: /manage/" in body

    sitemap = client.get("/sitemap.xml", HTTP_HOST="gsc.local")
    assert sitemap.status_code == 200
    xml = sitemap.content.decode()
    assert "<urlset" in xml
    assert "http://gsc.local/" in xml
    assert "http://gsc.local/products/" in xml
    assert "http://gsc.local/products/digital/" in xml
    assert "http://gsc.local/product/laptop/" in xml
    assert "http://gsc.local/page/about/" in xml
    assert "draft-item" not in xml


@pytest.mark.django_db
def test_google_html_verification_file(client, store):
    missing = client.get("/googleabc123.html", HTTP_HOST="gsc.local")
    assert missing.status_code == 404

    SeoService().save_google_verification(store, "googleabc123.html")
    found = client.get("/googleabc123.html", HTTP_HOST="gsc.local")
    assert found.status_code == 200
    assert found.content.decode().strip() == "google-site-verification: googleabc123.html"
    html = client.get("/", HTTP_HOST="gsc.local").content.decode()
    assert 'name="google-site-verification"' not in html
