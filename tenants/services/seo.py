"""Per-store SEO helpers: Google Search Console verification, sitemap, robots."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Iterable
from xml.sax.saxutils import escape

from django.http import HttpRequest
from django.utils import timezone

from tenants.models import Store
from tenants.services.cache import StoreCacheService
from tenants.services.store_config import SEO_GROUP, _as_str, _get_setting, _set_setting

GOOGLE_VERIFICATION_KEY = "google_site_verification"
GOOGLE_HTML_FILE_KEY = "google_html_file"

_META_CONTENT_RE = re.compile(
    r"""<meta\b[^>]*\b(?:name|content)\s*=\s*['"][^'"]*['"][^>]*>""",
    re.IGNORECASE,
)
_CONTENT_ATTR_RE = re.compile(
    r"""content\s*=\s*['"]([^'"]+)['"]""",
    re.IGNORECASE,
)
_NAME_ATTR_RE = re.compile(
    r"""name\s*=\s*['"]google-site-verification['"]""",
    re.IGNORECASE,
)
_HTML_FILE_RE = re.compile(r"^google([A-Za-z0-9_-]+)\.html$", re.IGNORECASE)
_FILE_LINE_RE = re.compile(
    r"google-site-verification:\s*(google[A-Za-z0-9_-]+\.html)",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{8,200}$")

SITEMAP_MAX_URLS = 50000

ROBOTS_DISALLOW = (
    "/manage/",
    "/cart/",
    "/checkout/",
    "/dashboard/",
    "/profile/",
    "/orders/",
    "/wishlist/",
    "/login/",
    "/register/",
    "/api/",
    "/admin/",
)


class SeoError(ValueError):
    """Invalid Search Console verification input."""


def parse_google_verification(raw: str) -> tuple[str, str]:
    """Return (meta_token, html_filename) from pasted GSC snippet or token.

    Accepts a bare token, a full HTML meta tag, a googleXXXX.html filename,
    or the HTML-file verification body Google provides.
    """
    text = (raw or "").strip()
    if not text:
        return "", ""

    file_line = _FILE_LINE_RE.search(text)
    if file_line:
        return "", file_line.group(1).lower()

    file_match = _HTML_FILE_RE.match(text)
    if file_match:
        return "", text.lower()

    if "google-site-verification" in text.lower() and "<meta" in text.lower():
        for tag in _META_CONTENT_RE.findall(text):
            if not _NAME_ATTR_RE.search(tag):
                continue
            content = _CONTENT_ATTR_RE.search(tag)
            if content:
                token = content.group(1).strip()
                if not _TOKEN_RE.match(token):
                    raise SeoError("کد تأیید گوگل نامعتبر است")
                return token, ""
        raise SeoError("تگ تأیید گوگل پیدا نشد")

    if _TOKEN_RE.match(text) and not text.lower().endswith(".html"):
        return text, ""

    raise SeoError("کد تأیید گوگل را به‌صورت تگ HTML، توکن، یا نام فایل google….html وارد کنید")


def _lastmod(value: datetime | None) -> str:
    if not value:
        return ""
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return timezone.localtime(value).date().isoformat()


def _origin_from_request(request: HttpRequest | None) -> str:
    if request is None:
        return ""
    return request.build_absolute_uri("/").rstrip("/")


class SeoService:
    """Load/save Google Search Console settings and emit crawl files."""

    def __init__(self):
        self.cache_service = StoreCacheService()

    def get_verification_token(self, store: Store | None) -> str:
        if not store or not store.pk:
            return ""
        return _as_str(_get_setting(store, SEO_GROUP, GOOGLE_VERIFICATION_KEY, ""))

    def get_html_filename(self, store: Store | None) -> str:
        if not store or not store.pk:
            return ""
        return _as_str(_get_setting(store, SEO_GROUP, GOOGLE_HTML_FILE_KEY, "")).lower()

    def get_storefront_defaults(self, store: Store | None) -> dict[str, str]:
        if not store or not store.pk:
            return {
                "meta_title": "",
                "meta_description": "",
                "meta_keywords": "",
                "og_image": "",
                "robots": "index,follow",
                "canonical_url": "",
                "head_scripts": "",
                "footer_scripts": "",
            }
        return {
            "meta_title": _as_str(_get_setting(store, SEO_GROUP, "meta_title", "")),
            "meta_description": _as_str(_get_setting(store, SEO_GROUP, "meta_description", "")),
            "meta_keywords": _as_str(_get_setting(store, SEO_GROUP, "meta_keywords", "")),
            "og_image": _as_str(_get_setting(store, SEO_GROUP, "og_image", "")),
            "robots": _as_str(_get_setting(store, SEO_GROUP, "robots", "")) or "index,follow",
            "canonical_url": _as_str(_get_setting(store, SEO_GROUP, "canonical_url", "")),
            "head_scripts": "",
            "footer_scripts": "",
        }

    def get_overview(self, store: Store, request: HttpRequest | None = None) -> dict[str, Any]:
        token = self.get_verification_token(store)
        html_file = self.get_html_filename(store)
        origin = _origin_from_request(request)
        return {
            "google_site_verification": token,
            "google_html_file": html_file,
            "verification_configured": bool(token or html_file),
            "sitemap_url": f"{origin}/sitemap.xml" if origin else "/sitemap.xml",
            "robots_url": f"{origin}/robots.txt" if origin else "/robots.txt",
            "html_file_url": f"{origin}/{html_file}" if origin and html_file else "",
        }

    def save_google_verification(self, store: Store, raw: str) -> dict[str, Any]:
        token, html_file = parse_google_verification(raw)
        _set_setting(
            store,
            SEO_GROUP,
            GOOGLE_VERIFICATION_KEY,
            token,
            description="کد تأیید HTML tag گوگل سرچ کنسول",
        )
        _set_setting(
            store,
            SEO_GROUP,
            GOOGLE_HTML_FILE_KEY,
            html_file,
            description="فایل تأیید HTML گوگل سرچ کنسول",
        )
        self.cache_service.invalidate_store(store)
        return {"google_site_verification": token, "google_html_file": html_file}

    def matches_html_file(self, store: Store, filename: str) -> bool:
        stored = self.get_html_filename(store)
        return bool(stored) and stored == filename.lower()

    def html_file_body(self, filename: str) -> str:
        return f"google-site-verification: {filename.lower()}\n"

    def robots_txt(self, store: Store, request: HttpRequest) -> str:
        origin = _origin_from_request(request)
        lines = ["User-agent: *", "Allow: /"]
        lines.extend(f"Disallow: {path}" for path in ROBOTS_DISALLOW)
        lines.append("")
        lines.append(f"Sitemap: {origin}/sitemap.xml")
        lines.append("")
        return "\n".join(lines)

    def sitemap_xml(self, store: Store, request: HttpRequest) -> str:
        origin = _origin_from_request(request)
        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        count = 0
        for entry in self._iter_sitemap_entries(store, origin):
            count += 1
            if count > SITEMAP_MAX_URLS:
                break
            parts.append("  <url>")
            parts.append(f"    <loc>{escape(entry['loc'])}</loc>")
            if entry.get("lastmod"):
                parts.append(f"    <lastmod>{escape(entry['lastmod'])}</lastmod>")
            if entry.get("changefreq"):
                parts.append(f"    <changefreq>{escape(entry['changefreq'])}</changefreq>")
            if entry.get("priority"):
                parts.append(f"    <priority>{escape(entry['priority'])}</priority>")
            parts.append("  </url>")
        parts.append("</urlset>")
        parts.append("")
        return "\n".join(parts)

    def _iter_sitemap_entries(self, store: Store, origin: str) -> Iterable[dict[str, str]]:
        from blog.models import BlogPost
        from blog.services.blog import BlogService
        from cms.models import Page
        from products.enums import ProductStatus
        from products.models import Category, Product

        yield {
            "loc": f"{origin}/",
            "changefreq": "daily",
            "priority": "1.0",
            "lastmod": _lastmod(getattr(store, "updated_at", None)),
        }
        yield {
            "loc": f"{origin}/products/",
            "changefreq": "daily",
            "priority": "0.8",
        }

        for slug, updated in (
            Category.objects.filter(store=store, is_active=True)
            .order_by("sort_order", "slug")
            .values_list("slug", "updated_at")
            .iterator()
        ):
            yield {
                "loc": f"{origin}/products/{slug}/",
                "lastmod": _lastmod(updated),
                "changefreq": "weekly",
                "priority": "0.7",
            }

        for slug, updated in (
            Product.objects.filter(store=store, status=ProductStatus.ACTIVE)
            .order_by("id")
            .values_list("slug", "updated_at")
            .iterator()
        ):
            yield {
                "loc": f"{origin}/product/{slug}/",
                "lastmod": _lastmod(updated),
                "changefreq": "weekly",
                "priority": "0.8",
            }

        for slug, updated in (
            Page.objects.filter(store=store, is_published=True)
            .order_by("sort_order", "slug")
            .values_list("slug", "updated_at")
            .iterator()
        ):
            yield {
                "loc": f"{origin}/page/{slug}/",
                "lastmod": _lastmod(updated),
                "changefreq": "monthly",
                "priority": "0.5",
            }

        if BlogService().is_active(store):
            yield {
                "loc": f"{origin}/blog/",
                "changefreq": "weekly",
                "priority": "0.6",
            }
            for slug, updated in (
                BlogPost.objects.filter(store=store, is_published=True)
                .order_by("-published_at", "-id")
                .values_list("slug", "updated_at")
                .iterator()
            ):
                yield {
                    "loc": f"{origin}/blog/{slug}/",
                    "lastmod": _lastmod(updated),
                    "changefreq": "weekly",
                    "priority": "0.6",
                }
