"""CMS service layer."""

from django.utils import timezone

from cms.models import Banner, ContentBlock, LayoutSettings, Menu, MenuItem, Page, Slide, Slider, Widget
from cms.services.cache import CMSCacheService
from cms.services.shortcodes import expand_shortcodes
from core.cache import cache_manager
from core.cache.keys import cms_page


class CMSService:
    """Fetch and manage CMS content per store."""

    def __init__(self):
        self.cache = CMSCacheService()

    def get_layout(self, store) -> dict:
        cached = self.cache.get(store.id, "layout")
        if cached is not None:
            return cached

        layout, _ = LayoutSettings.objects.get_or_create(store=store)
        data = {
            "use_custom_header": layout.use_custom_header,
            "use_custom_footer": layout.use_custom_footer,
            "header_html": layout.header_html,
            "footer_html": layout.footer_html,
        }
        self.cache.set(store.id, "layout", data)
        return data

    def get_menus(self, store) -> dict:
        cached = self.cache.get(store.id, "menus")
        if cached is not None:
            return cached

        menus = {}
        for menu in Menu.objects.filter(store=store, is_active=True).prefetch_related("items"):
            items = self._build_menu_tree(menu.items.filter(parent__isnull=True, is_active=True))
            menus[menu.location] = {
                "name": menu.name,
                "location": menu.location,
                "items": items,
            }
        self.cache.set(store.id, "menus", menus)
        return menus

    def _build_menu_tree(self, items) -> list:
        result = []
        for item in items.order_by("sort_order"):
            node = {
                "id": item.id,
                "label": item.label,
                "url": item.href,
                "open_new_tab": item.open_new_tab,
                "children": self._build_menu_tree(item.children.filter(is_active=True)),
            }
            result.append(node)
        return result

    def get_banners(self, store, position: str | None = None) -> list:
        cached = self.cache.get(store.id, "banners")
        if cached is None:
            banners = Banner.objects.filter(store=store, is_active=True).order_by("sort_order")
            cached = {}
            for b in banners:
                if b.is_visible:
                    cached.setdefault(b.position, []).append(self._serialize_banner(b))
            self.cache.set(store.id, "banners", cached)

        if position:
            return cached.get(position, [])
        return cached

    def _serialize_banner(self, banner: Banner) -> dict:
        return {
            "id": banner.id,
            "title": banner.title,
            "subtitle": banner.subtitle,
            "image": banner.image,
            "link": banner.link,
            "position": banner.position,
        }

    def get_slider(self, store, slug: str = "home") -> dict | None:
        sliders_cache = self.cache.get(store.id, "sliders")
        if sliders_cache is None:
            sliders_cache = {}
            for slider in Slider.objects.filter(store=store, is_active=True).prefetch_related("slides"):
                sliders_cache[slider.slug] = self._serialize_slider(slider)
            self.cache.set(store.id, "sliders", sliders_cache)
        return sliders_cache.get(slug)

    def _serialize_slider(self, slider: Slider) -> dict:
        slides = [
            {
                "id": s.id,
                "title": s.title,
                "subtitle": s.subtitle,
                "image": s.image,
                "link": s.link,
            }
            for s in slider.slides.filter(is_active=True).order_by("sort_order")
        ]
        return {
            "id": slider.id,
            "name": slider.name,
            "slug": slider.slug,
            "autoplay": slider.autoplay,
            "interval": slider.interval,
            "slides": slides,
        }

    def get_page(self, store, slug: str) -> Page | None:
        try:
            return Page.objects.prefetch_related("blocks").get(
                store=store, slug=slug, is_published=True
            )
        except Page.DoesNotExist:
            return None

    def get_published_page_payload(self, store, slug: str) -> dict | None:
        """Serialized published page for storefront (cached)."""
        cache_key = cms_page(store.id, slug)

        def factory():
            page = self.get_page(store, slug)
            if not page:
                return None
            return self.serialize_page(page, render_content=True)

        # Cache None as sentinel so repeated misses don't thrash DB.
        cached = cache_manager.get(cache_key)
        if cached is not None:
            return None if cached == "__missing__" else cached

        payload = factory()
        cache_manager.set(cache_key, payload if payload is not None else "__missing__", ttl="medium")
        return payload

    def serialize_page(self, page: Page, *, render_content: bool = True) -> dict:
        store = page.store
        blocks = []
        for b in page.blocks.filter(is_active=True).order_by("sort_order"):
            content = b.content
            if render_content and isinstance(content, dict):
                content = dict(content)
                if "html" in content and isinstance(content["html"], str):
                    content["html"] = expand_shortcodes(content["html"], store)
                if "text" in content and isinstance(content["text"], str):
                    content["text"] = expand_shortcodes(content["text"], store)
            blocks.append(
                {
                    "id": b.id,
                    "type": b.block_type,
                    "title": b.title,
                    "content": content,
                    "widget_slug": b.widget.slug if b.widget else None,
                }
            )
        raw = page.content or ""
        return {
            "id": page.id,
            "title": page.title,
            "slug": page.slug,
            "content": expand_shortcodes(raw, store) if render_content else raw,
            "is_published": page.is_published,
            "meta_title": page.meta_title,
            "meta_description": page.meta_description,
            "blocks": blocks,
            "seo": self.serialize_seo(page),
        }

    def serialize_seo(self, obj) -> dict:
        return {
            "meta_title": getattr(obj, "meta_title", ""),
            "meta_description": getattr(obj, "meta_description", ""),
            "meta_keywords": getattr(obj, "meta_keywords", ""),
            "og_image": getattr(obj, "og_image", ""),
            "canonical_url": getattr(obj, "canonical_url", ""),
            "robots": getattr(obj, "robots", "index,follow"),
            "head_scripts": getattr(obj, "head_scripts", ""),
            "footer_scripts": getattr(obj, "footer_scripts", ""),
        }

    def get_storefront_context(self, store) -> dict:
        # Layout first: get_or_create may fire signals that invalidate CMS cache.
        layout = self.get_layout(store)
        return {
            "cms_menus": self.get_menus(store),
            "cms_banners": self.get_banners(store),
            "cms_slider": self.get_slider(store, "home"),
            "cms_layout": layout,
        }

    def list_pages(self, store):
        return Page.objects.filter(store=store).order_by("sort_order", "title")

    def list_widgets(self, store):
        return Widget.objects.filter(store=store, is_active=True)
