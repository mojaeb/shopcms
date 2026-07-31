"""Store Admin CMS API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from cms.enums import BannerPosition, MenuLocation
from cms.models import Banner, LayoutSettings, Menu, MenuItem, Page, Shortcode, Slide, Slider
from cms.services.cms import CMSService
from cms.services.shortcodes import invalidate_shortcode_cache, list_shortcodes_for_admin
from dashboard.authentication_store import store_admin_auth
from tenants.context import get_current_store

router = Router(auth=store_admin_auth)
cms = CMSService()


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


class PageCreateSchema(Schema):
    title: str
    slug: str
    content: str = ""
    is_published: bool = True
    meta_title: str = ""
    meta_description: str = ""


class PageUpdateSchema(Schema):
    title: str | None = None
    slug: str | None = None
    content: str | None = None
    is_published: bool | None = None
    meta_title: str | None = None
    meta_description: str | None = None


class MenuItemCreateSchema(Schema):
    label: str
    url: str = ""
    parent_id: int | None = None
    sort_order: int = 0
    open_new_tab: bool = False


class BannerCreateSchema(Schema):
    title: str
    subtitle: str = ""
    image: str = ""
    link: str = ""
    position: str = BannerPosition.HOME_TOP
    sort_order: int = 0
    is_active: bool = True


class SliderCreateSchema(Schema):
    name: str
    slug: str
    autoplay: bool = True
    interval: int = 5000


class SlideCreateSchema(Schema):
    title: str = ""
    subtitle: str = ""
    image: str
    link: str = ""
    sort_order: int = 0


class LayoutUpdateSchema(Schema):
    header_html: str = ""
    footer_html: str = ""
    use_custom_header: bool = False
    use_custom_footer: bool = False


class ShortcodeCreateSchema(Schema):
    name: str
    label: str
    description: str = ""
    html_template: str
    is_self_closing: bool = False
    example: str = ""
    is_active: bool = True


class ShortcodeUpdateSchema(Schema):
    name: str | None = None
    label: str | None = None
    description: str | None = None
    html_template: str | None = None
    is_self_closing: bool | None = None
    example: str | None = None
    is_active: bool | None = None


def _normalize_shortcode_name(name: str) -> str:
    cleaned = (name or "").strip().lower().replace(" ", "-")
    if not cleaned or not cleaned[0].isalpha():
        raise HttpError(400, "نام shortcode باید با حرف شروع شود")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(ch not in allowed for ch in cleaned):
        raise HttpError(400, "نام shortcode فقط حروف، عدد، - و _")
    return cleaned


@router.get("/pages")
def list_pages(request):
    store = _store(request)
    return [
        {
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "is_published": p.is_published,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in cms.list_pages(store)
    ]


@router.post("/pages")
def create_page(request, payload: PageCreateSchema):
    store = _store(request)
    if Page.objects.filter(store=store, slug=payload.slug).exists():
        raise HttpError(400, "این شناسه قبلاً استفاده شده")
    page = Page.objects.create(
        store=store,
        title=payload.title,
        slug=payload.slug,
        content=payload.content,
        is_published=payload.is_published,
        meta_title=payload.meta_title,
        meta_description=payload.meta_description,
    )
    return cms.serialize_page(page, render_content=False)


@router.get("/pages/{page_id}")
def get_page(request, page_id: int):
    store = _store(request)
    try:
        page = Page.objects.prefetch_related("blocks").get(pk=page_id, store=store)
    except Page.DoesNotExist:
        raise HttpError(404, "صفحه یافت نشد")
    return cms.serialize_page(page, render_content=False)


@router.put("/pages/{page_id}")
def update_page(request, page_id: int, payload: PageUpdateSchema):
    store = _store(request)
    try:
        page = Page.objects.get(pk=page_id, store=store)
    except Page.DoesNotExist:
        raise HttpError(404, "صفحه یافت نشد")
    data = {k: v for k, v in payload.dict().items() if v is not None}
    if "slug" in data and Page.objects.filter(store=store, slug=data["slug"]).exclude(pk=page.id).exists():
        raise HttpError(400, "این شناسه قبلاً استفاده شده")
    for field, value in data.items():
        setattr(page, field, value)
    page.save()
    return cms.serialize_page(page, render_content=False)


@router.delete("/pages/{page_id}")
def delete_page(request, page_id: int):
    store = _store(request)
    deleted, _ = Page.objects.filter(pk=page_id, store=store).delete()
    if not deleted:
        raise HttpError(404, "صفحه یافت نشد")
    return {"success": True}


@router.get("/shortcodes")
def list_shortcodes(request):
    store = _store(request)
    return list_shortcodes_for_admin(store)


@router.post("/shortcodes")
def create_shortcode(request, payload: ShortcodeCreateSchema):
    store = _store(request)
    name = _normalize_shortcode_name(payload.name)
    if Shortcode.objects.filter(store=store, name=name).exists():
        raise HttpError(400, "این shortcode از قبل وجود دارد")
    if not (payload.html_template or "").strip():
        raise HttpError(400, "قالب HTML الزامی است")
    sc = Shortcode.objects.create(
        store=store,
        name=name,
        label=payload.label.strip() or name,
        description=payload.description,
        html_template=payload.html_template,
        is_self_closing=payload.is_self_closing,
        example=payload.example,
        is_active=payload.is_active,
    )
    invalidate_shortcode_cache(store)
    return {
        "id": sc.id,
        "name": sc.name,
        "label": sc.label,
        "description": sc.description,
        "html_template": sc.html_template,
        "is_self_closing": sc.is_self_closing,
        "example": sc.example,
        "is_active": sc.is_active,
        "is_system": False,
    }


@router.put("/shortcodes/{shortcode_id}")
def update_shortcode(request, shortcode_id: int, payload: ShortcodeUpdateSchema):
    store = _store(request)
    try:
        sc = Shortcode.objects.get(pk=shortcode_id, store=store)
    except Shortcode.DoesNotExist:
        raise HttpError(404, "شورت‌کد یافت نشد")
    data = {k: v for k, v in payload.dict().items() if v is not None}
    if "name" in data:
        data["name"] = _normalize_shortcode_name(data["name"])
        if Shortcode.objects.filter(store=store, name=data["name"]).exclude(pk=sc.id).exists():
            raise HttpError(400, "این shortcode از قبل وجود دارد")
    for field, value in data.items():
        setattr(sc, field, value)
    sc.save()
    invalidate_shortcode_cache(store)
    return {
        "id": sc.id,
        "name": sc.name,
        "label": sc.label,
        "description": sc.description,
        "html_template": sc.html_template,
        "is_self_closing": sc.is_self_closing,
        "example": sc.example,
        "is_active": sc.is_active,
        "is_system": False,
    }


@router.delete("/shortcodes/{shortcode_id}")
def delete_shortcode(request, shortcode_id: int):
    store = _store(request)
    deleted, _ = Shortcode.objects.filter(pk=shortcode_id, store=store).delete()
    if not deleted:
        raise HttpError(404, "شورت‌کد یافت نشد")
    invalidate_shortcode_cache(store)
    return {"success": True}


@router.get("/menus")
def list_menus(request):
    store = _store(request)
    return cms.get_menus(store)


@router.post("/menus/{location}/items")
def add_menu_item(request, location: str, payload: MenuItemCreateSchema):
    store = _store(request)
    if location not in MenuLocation.values:
        raise HttpError(400, "مکان منو نامعتبر است")
    menu, _ = Menu.objects.get_or_create(
        store=store,
        location=location,
        defaults={"name": location, "is_active": True},
    )
    parent = None
    if payload.parent_id:
        parent = MenuItem.objects.get(pk=payload.parent_id, menu=menu)
    item = MenuItem.objects.create(
        menu=menu,
        parent=parent,
        label=payload.label,
        url=payload.url,
        sort_order=payload.sort_order,
        open_new_tab=payload.open_new_tab,
    )
    return {"id": item.id, "label": item.label, "url": item.href}


@router.get("/banners")
def list_banners(request):
    store = _store(request)
    return cms.get_banners(store)


@router.post("/banners")
def create_banner(request, payload: BannerCreateSchema):
    store = _store(request)
    banner = Banner.objects.create(store=store, **payload.dict())
    return {"id": banner.id, "title": banner.title}


@router.get("/sliders")
def list_sliders(request):
    store = _store(request)
    sliders = Slider.objects.filter(store=store, is_active=True)
    return [{"id": s.id, "name": s.name, "slug": s.slug} for s in sliders]


@router.post("/sliders")
def create_slider(request, payload: SliderCreateSchema):
    store = _store(request)
    slider = Slider.objects.create(store=store, **payload.dict())
    return {"id": slider.id, "slug": slider.slug}


@router.post("/sliders/{slider_id}/slides")
def add_slide(request, slider_id: int, payload: SlideCreateSchema):
    store = _store(request)
    slider = Slider.objects.get(pk=slider_id, store=store)
    slide = Slide.objects.create(slider=slider, **payload.dict())
    return {"id": slide.id}


@router.get("/layout")
def get_layout(request):
    return cms.get_layout(_store(request))


@router.put("/layout")
def update_layout(request, payload: LayoutUpdateSchema):
    store = _store(request)
    layout, _ = LayoutSettings.objects.get_or_create(store=store)
    for field, value in payload.dict().items():
        setattr(layout, field, value)
    layout.save()
    return cms.get_layout(store)
