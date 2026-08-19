"""In-admin documentation hub (sidebar «مستندات»)."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse

from tenants.services.advanced_settings import (
    copyable_snippet_categories,
    list_copyable_snippets,
)

# slug → metadata for sidebar + index cards
DOC_PAGES: tuple[dict[str, str], ...] = (
    {
        "slug": "overview",
        "title": "نمای کلی تنظیمات",
        "icon": "menu_book",
        "summary": "کدام تنظیم در تب فرم است و کدام در JSON پیشرفته.",
    },
    {
        "slug": "json-templates",
        "title": "کتابخانه قالب‌های JSON",
        "icon": "data_object",
        "summary": "قالب‌های آماده برای کپی در تنظیمات پیشرفته و config روش ارسال.",
    },
    {
        "slug": "payment",
        "title": "پرداخت و زرین‌پال",
        "icon": "payments",
        "summary": "درگاه‌ها، Callback، URLهای API و حالت آزمایشی.",
    },
    {
        "slug": "shipping",
        "title": "ارسال و تعرفه",
        "icon": "local_shipping",
        "summary": "وزن بسته، منطقه، پیک، پس‌کرایه، سقف وزن پست، import/export گروهی تعرفه و محاسبه فاصله با GPS.",
    },
    {
        "slug": "location",
        "title": "موقعیت مکانی و فاصله",
        "icon": "location_on",
        "summary": "تنظیم مختصات GPS مبدا فروشگاه، محاسبه فاصله واقعی برای تعرفه مسافتی و ویجت GPS چک‌اوت.",
    },
    {
        "slug": "notifications",
        "title": "اعلان‌ها و پیامک",
        "icon": "notifications",
        "summary": "پیامک وضعیت مرسوله (SHIPPED/DELIVERED) و تنظیم کانال SMS فروشگاه.",
    },
)


def docs_index_url() -> str:
    return reverse("admin:shopcms_docs")


def docs_page_url(slug: str) -> str:
    return reverse("admin:shopcms_docs_page", kwargs={"slug": slug})


def _page_meta(slug: str) -> dict[str, str]:
    for page in DOC_PAGES:
        if page["slug"] == slug:
            return page
    raise Http404("مستند یافت نشد")


def _base_context(request: HttpRequest, *, title: str, active_slug: str = "") -> dict:
    return {
        **admin.site.each_context(request),
        "title": title,
        "doc_pages": DOC_PAGES,
        "active_doc_slug": active_slug,
        "docs_index_url": docs_index_url(),
    }


@staff_member_required
def docs_index(request: HttpRequest) -> HttpResponse:
    context = _base_context(request, title="مستندات ShopCMS", active_slug="")
    return TemplateResponse(request, "admin/docs/index.html", context)


@staff_member_required
def docs_page(request: HttpRequest, slug: str) -> HttpResponse:
    meta = _page_meta(slug)
    context = _base_context(request, title=meta["title"], active_slug=slug)
    context["doc"] = meta

    if slug == "json-templates":
        snippets = list_copyable_snippets()
        context["setting_snippets"] = snippets
        context["setting_snippet_categories"] = copyable_snippet_categories(snippets)
        template = "admin/docs/json_templates.html"
    elif slug == "payment":
        template = "admin/docs/payment.html"
    elif slug == "shipping":
        template = "admin/docs/shipping.html"
    elif slug == "location":
        template = "admin/docs/location.html"
    elif slug == "notifications":
        template = "admin/docs/notifications.html"
    else:
        template = "admin/docs/overview.html"

    return TemplateResponse(request, template, context)


def get_docs_urls() -> list:
    return [
        path("docs/", admin.site.admin_view(docs_index), name="shopcms_docs"),
        path("docs/<slug:slug>/", admin.site.admin_view(docs_page), name="shopcms_docs_page"),
    ]


def patch_admin_docs_urls() -> None:
    """Prepend docs routes onto the default AdminSite URLConf."""
    if getattr(admin.site, "_shopcms_docs_patched", False):
        return
    original_get_urls = admin.site.get_urls

    def get_urls():
        return get_docs_urls() + original_get_urls()

    admin.site.get_urls = get_urls  # type: ignore[method-assign]
    admin.site._shopcms_docs_patched = True  # type: ignore[attr-defined]
