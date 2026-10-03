"""CMS tests."""

import pytest

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.jwt import JWTService
from cms.enums import BannerPosition, MenuLocation
from cms.models import Banner, Menu, MenuItem, Page, Slide, Slider
from cms.services.cms import CMSService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="CMS Shop", slug="cms-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="cms.local")
    return s


@pytest.fixture
def cms_data(store):
    page = Page.objects.create(
        store=store, title="About", slug="about", content="<p>About us</p>", is_published=True,
        meta_title="About Us", meta_description="About page",
    )
    menu = Menu.objects.create(store=store, name="Header", location=MenuLocation.HEADER)
    MenuItem.objects.create(menu=menu, label="About", url="/page/about/")
    Banner.objects.create(
        store=store, title="Sale", position=BannerPosition.HOME_TOP,
        image="https://example.com/banner.jpg", is_active=True,
    )
    slider = Slider.objects.create(store=store, name="Home", slug="home", is_active=True)
    Slide.objects.create(slider=slider, title="Slide 1", image="https://example.com/slide.jpg")
    return {"page": page, "menu": menu, "slider": slider}


@pytest.fixture
def admin_token(store):
    role = Role.objects.create(name="Admin", codename="store_admin", scope=RoleScope.STORE, is_system=True)
    user = User.objects.create_user(phone="09129998877", is_staff=True)
    m = StoreMembership.objects.create(user=user, store=store, role=role, status=MembershipStatus.ACTIVE)
    return JWTService().create_tokens(user.id, store.id, "store_admin", m.id).access_token


@pytest.mark.django_db
def test_cms_service_menus(store, cms_data):
    cms = CMSService()
    menus = cms.get_menus(store)
    assert "header" in menus
    assert menus["header"]["items"][0]["label"] == "About"


@pytest.mark.django_db
def test_cms_service_banners(store, cms_data):
    cms = CMSService()
    banners = cms.get_banners(store, BannerPosition.HOME_TOP)
    assert len(banners) == 1
    assert banners[0]["title"] == "Sale"


@pytest.mark.django_db
def test_cms_service_slider(store, cms_data):
    cms = CMSService()
    slider = cms.get_slider(store, "home")
    assert slider is not None
    assert len(slider["slides"]) == 1


@pytest.mark.django_db
def test_cms_public_api(client, store, cms_data):
    response = client.get("/api/v1/cms/menus", HTTP_HOST="cms.local")
    assert response.status_code == 200
    assert "header" in response.json()

    response = client.get("/api/v1/cms/pages/about", HTTP_HOST="cms.local")
    assert response.status_code == 200
    assert response.json()["title"] == "About"


@pytest.mark.django_db
def test_cms_page_payload_cached(store, cms_data):
    from core.cache.keys import cms_page
    from django.core.cache import cache

    cms = CMSService()
    first = cms.get_published_page_payload(store, "about")
    assert first["title"] == "About"

    key = cms_page(store.id, "about")
    cache.set(key, {"id": 1, "title": "Cached About", "slug": "about", "content": "", "blocks": [], "seo": {}}, 60)
    second = cms.get_published_page_payload(store, "about")
    assert second["title"] == "Cached About"

    # Saving page invalidates cache
    page = cms_data["page"]
    page.title = "About Updated"
    page.save()
    third = cms.get_published_page_payload(store, "about")
    assert third["title"] == "About Updated"


@pytest.mark.django_db
def test_cms_page_view(client, store, cms_data):
    response = client.get("/page/about/", HTTP_HOST="cms.local")
    assert response.status_code == 200
    assert "About us" in response.content.decode()


@pytest.mark.django_db
def test_home_with_cms(client, store, cms_data):
    response = client.get("/", HTTP_HOST="cms.local")
    content = response.content.decode()
    assert response.status_code == 200
    assert "Sale" in content or "Slide 1" in content


@pytest.mark.django_db
def test_cms_admin_create_page(client, admin_token, store):
    response = client.post(
        "/api/v1/store-admin/cms/pages",
        data={"title": "Contact", "slug": "contact", "content": "Contact us"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="cms.local",
    )
    assert response.status_code == 200
    assert Page.objects.filter(store=store, slug="contact").exists()


@pytest.mark.django_db
def test_cms_admin_create_banner(client, admin_token, store):
    response = client.post(
        "/api/v1/store-admin/cms/banners",
        data={"title": "New Banner", "position": "home_top", "image": "/media/banner.jpg"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="cms.local",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New Banner"
    assert body["image"] == "/media/banner.jpg"
    assert Banner.objects.filter(store=store, title="New Banner").exists()


@pytest.mark.django_db
def test_cms_admin_lists_inactive_and_updates_banner(client, admin_token, store, cms_data):
    hidden = Banner.objects.create(
        store=store, title="Hidden", position=BannerPosition.SIDEBAR, is_active=False,
    )
    listing = client.get(
        "/api/v1/store-admin/cms/banners",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="cms.local",
    )
    assert listing.status_code == 200
    titles = [row["title"] for row in listing.json()]
    assert "Sale" in titles
    assert "Hidden" in titles

    response = client.put(
        f"/api/v1/store-admin/cms/banners/{hidden.id}",
        data={
            "title": "Hidden Updated",
            "position": "home_middle",
            "image": "/media/mid.jpg",
            "is_active": True,
            "sort_order": 3,
            "starts_at": "2026-10-01T10:00",
            "ends_at": "2026-10-31T10:00",
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="cms.local",
    )
    assert response.status_code == 200
    hidden.refresh_from_db()
    assert hidden.title == "Hidden Updated"
    assert hidden.position == BannerPosition.HOME_MIDDLE
    assert hidden.is_active is True
    assert hidden.image == "/media/mid.jpg"

    public = CMSService().get_banners(store, BannerPosition.HOME_MIDDLE)
    assert any(item["title"] == "Hidden Updated" for item in public)

    deleted = client.delete(
        f"/api/v1/store-admin/cms/banners/{hidden.id}",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="cms.local",
    )
    assert deleted.status_code == 200
    assert not Banner.objects.filter(pk=hidden.id).exists()


@pytest.mark.django_db
def test_cms_admin_rejects_bad_banner_position(client, admin_token, store):
    response = client.post(
        "/api/v1/store-admin/cms/banners",
        data={"title": "Bad", "position": "nowhere"},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="cms.local",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_manage_banners_page(client, store):
    role = Role.objects.create(name="Manager", codename="manager", scope=RoleScope.STORE, is_system=True)
    user = User.objects.create_user(phone="09121112233")
    StoreMembership.objects.create(user=user, store=store, role=role, status=MembershipStatus.ACTIVE)
    client.force_login(user)
    response = client.get("/manage/banners/", HTTP_HOST="cms.local")
    assert response.status_code == 200
    body = response.content.decode("utf-8")
    assert "بنر جدید" in body
    assert "store_admin/banners.js" in body
