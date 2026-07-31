"""Tests for per-store theme settings."""

import json

import pytest

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from tenants.models import Domain, Store, StoreSetting, Theme
from tenants.services.theme_settings import (
    DEFAULT_THEME_CONFIG,
    ThemeSettingsService,
    normalize_theme_config,
)


@pytest.fixture
def setup_store(db):
    theme = Theme.objects.create(
        name="Modern", slug="modern", directory="modern", is_default=True
    )
    store = Store.objects.create(
        name="Shop One", slug="shop1", theme=theme, default_theme=theme, status="active"
    )
    Domain.objects.create(store=store, domain="localhost", is_primary=True)
    return store


@pytest.fixture
def admin_token(db, setup_store):
    role = Role.objects.create(
        name="Admin", codename="store_admin", scope=RoleScope.STORE, is_system=True
    )
    Permission.objects.create(codename="settings.manage", name="Manage Settings", group="settings")
    user = User.objects.create_user(phone="09121112222", first_name="Admin", is_staff=True)
    membership = StoreMembership.objects.create(
        user=user,
        store=setup_store,
        role=role,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
    )
    return JWTService().create_tokens(
        user.id, setup_store.id, "store_admin", membership.id
    ).access_token


@pytest.mark.django_db
def test_normalize_fills_defaults():
    result = normalize_theme_config({"hero": {"slides": [{"title": "Hi"}]}})
    assert result["logo"] == ""
    assert result["colors"]["primary"] == "#0f766e"
    assert result["hero"]["slides"][0]["title"] == "Hi"
    assert result["hero"]["slides"][0]["button_text"] == "خرید کنید"
    assert result["trust_badges"]["enamad"]["image"] == ""
    assert result["trust_badges"]["badge2"]["link"] == ""
    # default button_link comes from DEFAULT_HERO_SLIDE
    assert result["hero"]["slides"][0]["button_link"] in ("/products/", "/category/")


@pytest.mark.django_db
def test_get_theme_settings_defaults(setup_store):
    config = ThemeSettingsService().get_theme_settings(setup_store)
    assert config == DEFAULT_THEME_CONFIG
    assert ThemeSettingsService().get_hero_slides(setup_store) == []


@pytest.mark.django_db
def test_update_and_get_theme_settings(setup_store):
    service = ThemeSettingsService()
    updated = service.update_theme_settings(
        setup_store,
        {
            "logo": "https://example.com/logo.png",
            "hero": {
                "slides": [
                    {
                        "image": "https://example.com/hero.jpg",
                        "thumbnail": "https://example.com/thumb.jpg",
                        "title": "عنوان",
                        "text": "متن",
                        "button_text": "بخر",
                        "button_link": "/category/sale/",
                        "background_color": "#112233",
                    }
                ]
            },
        },
    )
    assert updated["logo"] == "https://example.com/logo.png"
    assert updated["hero"]["slides"][0]["button_text"] == "بخر"

    setting = StoreSetting.objects.get(store=setup_store, group="theme", key="config")
    assert setting.value["hero"]["slides"][0]["image"] == "https://example.com/hero.jpg"

    slides = service.get_hero_slides(setup_store)
    assert len(slides) == 1
    assert slides[0]["thumbnail"] == "https://example.com/thumb.jpg"


@pytest.mark.django_db
def test_settings_overview_includes_theme(client, admin_token, setup_store):
    ThemeSettingsService().update_theme_settings(
        setup_store,
        {"hero": {"slides": [{"title": "From API", "image": "https://x.com/a.jpg"}]}},
    )
    response = client.get(
        "/api/v1/store-admin/settings",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200
    data = response.json()
    assert "theme" in data
    assert data["theme"]["hero"]["slides"][0]["title"] == "From API"


@pytest.mark.django_db
def test_put_theme_settings(client, admin_token, setup_store):
    payload = {
        "logo": "",
        "colors": {"primary": "#000000", "background": "#ffffff", "text": "#111111"},
        "hero": {
            "slides": [
                {
                    "image": "https://cdn.example.com/h.jpg",
                    "thumbnail": "https://cdn.example.com/t.jpg",
                    "title": "Hero",
                    "text": "Lead",
                    "button_text": "خرید",
                    "button_link": "/category/",
                    "background_color": "#f0f0f0",
                }
            ]
        },
    }
    response = client.put(
        "/api/v1/store-admin/settings/theme",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        HTTP_HOST="localhost",
    )
    assert response.status_code == 200, response.content.decode("utf-8")
    body = response.json()
    assert body["hero"]["slides"][0]["image"] == "https://cdn.example.com/h.jpg"
    assert body["colors"]["primary"] == "#000000"

    stored = ThemeSettingsService().get_theme_settings(setup_store)
    assert stored["hero"]["slides"][0]["button_text"] == "خرید"


@pytest.mark.django_db
def test_home_renders_theme_hero(client, setup_store):
    ThemeSettingsService().update_theme_settings(
        setup_store,
        {
            "hero": {
                "slides": [
                    {
                        "image": "https://cdn.example.com/h.jpg",
                        "thumbnail": "https://cdn.example.com/t.jpg",
                        "title": "Theme Hero Title",
                        "text": "Theme hero text",
                        "button_text": "خرید کنید",
                        "button_link": "/category/",
                        "background_color": "#f6f4f1",
                    }
                ]
            }
        },
    )
    response = client.get("/", HTTP_HOST="localhost")
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Theme Hero Title" in content
    assert "vg-theme-slide" in content
    assert "https://cdn.example.com/t.jpg" in content
