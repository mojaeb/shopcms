"""Tests for Unfold admin sidebar grouping."""

import pytest
from django.conf import settings
from django.test import RequestFactory

from accounts.models import User
from core.admin_navigation import can_view_model, get_navigation


def _group_map(nav: list[dict]) -> dict[str, dict]:
    return {group["title"]: group for group in nav}


@pytest.mark.django_db
def test_sidebar_keeps_platform_open_and_collapses_catalog():
    nav = get_navigation()
    groups = _group_map(nav)

    assert list(groups) == [
        "پلتفرم",
        "کاتالوگ فروشگاه",
        "داده‌های مشتری",
        "فروش و مالی",
        "محتوای فروشگاه",
        "سیستم",
    ]

    platform_titles = [item["title"] for item in groups["پلتفرم"]["items"]]
    assert groups["پلتفرم"].get("collapsible") is False
    assert "فروشگاه‌ها" in platform_titles
    assert "کاربران" in platform_titles
    assert "مدیرهای فروشگاه" in platform_titles
    assert "محصولات" not in platform_titles
    assert "برندها" not in platform_titles

    catalog = groups["کاتالوگ فروشگاه"]
    assert catalog["collapsible"] is True
    catalog_titles = [item["title"] for item in catalog["items"]]
    assert catalog_titles[:3] == ["محصولات", "دسته‌بندی‌ها", "برندها"]

    customers = groups["داده‌های مشتری"]
    assert customers["collapsible"] is True
    customer_titles = [item["title"] for item in customers["items"]]
    assert "سبدهای خرید" in customer_titles
    assert "آدرس‌ها" in customer_titles
    assert "کدهای OTP" in customer_titles

    for group in nav:
        for item in group["items"]:
            assert str(item["link"]).startswith("/admin/")


def test_unfold_sidebar_uses_navigation_callback():
    sidebar = settings.UNFOLD["SIDEBAR"]
    assert sidebar["navigation"] == "core.admin_navigation.get_navigation"
    assert sidebar["show_all_applications"] is True


@pytest.mark.django_db
def test_model_permission_allows_superuser_and_denies_anonymous():
    factory = RequestFactory()
    request = factory.get("/admin/")
    request.user = User.objects.create_superuser(phone="09120009999", password="x")
    assert can_view_model("products", "product")(request) is True

    anon = factory.get("/admin/")

    class Anon:
        is_authenticated = False
        is_superuser = False

        def has_perm(self, perm):
            return False

    anon.user = Anon()
    assert can_view_model("products", "product")(anon) is False
