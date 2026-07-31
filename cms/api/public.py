"""Public CMS API."""

from ninja import Router, Schema

from cms.services.cms import CMSService
from tenants.context import get_current_store

router = Router()
cms = CMSService()


class SeoSchema(Schema):
    meta_title: str = ""
    meta_description: str = ""
    meta_keywords: str = ""
    og_image: str = ""
    canonical_url: str = ""
    robots: str = "index,follow"


class PageSchema(Schema):
    id: int
    title: str
    slug: str
    content: str
    blocks: list
    seo: SeoSchema


@router.get("/menus")
def get_menus(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    return cms.get_menus(store)


@router.get("/banners")
def get_banners(request, position: str | None = None):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    return cms.get_banners(store, position)


@router.get("/sliders/{slug}")
def get_slider(request, slug: str):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    slider = cms.get_slider(store, slug)
    if not slider:
        return 404, {"detail": "اسلایدر یافت نشد"}
    return slider


@router.get("/pages/{slug}", response=PageSchema)
def get_page(request, slug: str):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    payload = cms.get_published_page_payload(store, slug)
    if not payload:
        return 404, {"detail": "صفحه یافت نشد"}
    return payload


@router.get("/layout")
def get_layout(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    return cms.get_layout(store)
