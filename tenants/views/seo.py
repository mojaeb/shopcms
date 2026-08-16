"""Public SEO crawl endpoints: robots.txt, sitemap.xml, Google verification file."""

from django.http import Http404, HttpResponse

from tenants.context import get_current_store
from tenants.services.seo import SeoService

seo_service = SeoService()


def _require_store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise Http404("فروشگاه یافت نشد")
    return store


def robots_txt(request):
    store = _require_store(request)
    return HttpResponse(seo_service.robots_txt(store, request), content_type="text/plain")


def sitemap_xml(request):
    store = _require_store(request)
    return HttpResponse(seo_service.sitemap_xml(store, request), content_type="application/xml")


def google_html_verification(request, token: str):
    store = _require_store(request)
    filename = f"google{token}.html"
    if not seo_service.matches_html_file(store, filename):
        raise Http404("فایل تأیید گوگل یافت نشد")
    return HttpResponse(seo_service.html_file_body(filename), content_type="text/html")
