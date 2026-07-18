"""Store Admin CMS API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from cms.enums import BannerPosition, MenuLocation
from cms.models import Banner, ContentBlock, LayoutSettings, Menu, MenuItem, Page, Slide, Slider, Widget
from cms.services.cms import CMSService
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


@router.get("/pages")
def list_pages(request):
    store = _store(request)
    return [
        {"id": p.id, "title": p.title, "slug": p.slug, "is_published": p.is_published}
        for p in cms.list_pages(store)
    ]


@router.post("/pages")
def create_page(request, payload: PageCreateSchema):
    store = _store(request)
    page = Page.objects.create(
        store=store,
        title=payload.title,
        slug=payload.slug,
        content=payload.content,
        is_published=payload.is_published,
        meta_title=payload.meta_title,
        meta_description=payload.meta_description,
    )
    return {"id": page.id, "slug": page.slug}


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
