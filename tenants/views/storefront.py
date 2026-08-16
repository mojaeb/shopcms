"""Storefront views with theme engine."""

from urllib.parse import quote

from django.http import Http404
from django.shortcuts import redirect

from tenants.context import get_current_store
from tenants.theme.engine import ThemeEngine

engine = ThemeEngine()


def _require_store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store and not request.GET.get("preview"):
        raise Http404("فروشگاه یافت نشد")
    return store


def _login_redirect(request):
    next_url = quote(request.get_full_path())
    return redirect(f"/login/?next={next_url}")


def storefront_category_redirect(request, slug=None):
    """Permanent redirect from legacy /category/ URLs to /products/."""
    target = f"/products/{slug}/" if slug else "/products/"
    if request.META.get("QUERY_STRING"):
        target = f"{target}?{request.META['QUERY_STRING']}"
    return redirect(target, permanent=True)


def storefront_home(request):
    store = _require_store(request)
    extra = {}
    if store:
        from cms.services.cms import CMSService
        from products.services.product import ProductService

        extra = CMSService().get_storefront_context(store)
        ps = ProductService()
        categories = list(ps.list_categories(store)[:10])
        # Prefer custom-flagged categories first for Pulse home strip
        categories = sorted(
            categories,
            key=lambda c: (0 if getattr(c, "is_custom", False) else 1, c.sort_order, c.name),
        )
        catalog = [ps.serialize_product_list(p) for p in ps.list_products(store)[:64]]

        home_sections = []
        active_cats = []
        for c in categories:
            items = [p for p in catalog if p.get("category_id") == c.id][:8]
            cat_payload = {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "image": getattr(c, "image", "") or "",
                "is_custom": bool(getattr(c, "is_custom", False)),
            }
            if items:
                active_cats.append(cat_payload)
                home_sections.append({**cat_payload, "products": items})

        deals = [p for p in catalog if p.get("discount_percent")][:12]
        if len(deals) < 4:
            featured = [p for p in catalog if p.get("is_featured")]
            deals = (deals + [p for p in featured if p not in deals])[:12]

        extra["home_categories"] = active_cats or [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "image": getattr(c, "image", "") or "",
                "is_custom": bool(getattr(c, "is_custom", False)),
            }
            for c in categories
        ]
        extra["home_sections"] = home_sections
        extra["home_deals"] = deals
        extra["home_products"] = catalog[:16]

        from django.utils import formats, timezone

        from blog.services.blog import BlogService

        bs = BlogService()
        if bs.is_active(store):
            home_posts = []
            for p in bs.list_published_posts(store)[:3]:
                item = bs.serialize_post_list(p)
                if p.published_at:
                    item["published_label"] = formats.date_format(
                        timezone.localtime(p.published_at), "DATE_FORMAT"
                    )
                else:
                    item["published_label"] = ""
                home_posts.append(item)
            extra["home_blog_posts"] = home_posts
        else:
            extra["home_blog_posts"] = []

        from tenants.services.seo import SeoService

        extra["seo"] = SeoService().get_storefront_defaults(store)
    return engine.render_page(request, "home", extra)


def storefront_cms_page(request, slug):
    store = _require_store(request)
    from cms.services.cms import CMSService
    cms = CMSService()
    page = cms.get_page(store, slug)
    if not page:
        raise Http404("صفحه یافت نشد")
    context = {"page": cms.serialize_page(page), "seo": cms.serialize_seo(page)}
    context.update(cms.get_storefront_context(store))
    return engine.render(request, "cms_page.html", context)


def storefront_category(request, slug=None):
    store = _require_store(request)
    from products.services.product import ProductService
    from products.services.search import ProductSearchService

    ps = ProductService()
    ss = ProductSearchService()
    categories = ps.list_categories(store)
    category = None
    if slug:
        category = categories.filter(slug=slug).first()
    products = ps.list_products(store, category_slug=slug)[:20] if slug else ps.list_products(store)[:20]
    context = {
        "category_slug": slug,
        "category": category,
        "categories": [
            {
                "name": c.name,
                "slug": c.slug,
                "image": getattr(c, "image", "") or "",
                "description": getattr(c, "description", "") or "",
            }
            for c in categories
        ],
        "products": [ps.serialize_product_list(p) for p in products],
        "filter_options": ss.get_filter_options(store, category_slug=slug),
        "query": "",
    }
    return engine.render_page(request, "category", context)


def storefront_search(request):
    store = _require_store(request)
    from products.services.product import ProductService
    from products.services.search import ProductSearchService

    query = request.GET.get("q", "")
    ps = ProductService()
    ss = ProductSearchService()
    products = ps.list_products(store, search=query)[:20]
    context = {
        "query": query,
        "products": [ps.serialize_product_list(p) for p in products],
        "filter_options": ss.get_filter_options(store),
        "category_slug": "",
    }
    return engine.render_page(request, "search", context)


def storefront_product(request, slug):
    store = _require_store(request)
    from products.services.product import ProductService

    ps = ProductService()
    product = ps.get_product(store, slug)
    if not product:
        raise Http404("محصول یافت نشد")
    detail = ps.serialize_product_detail(product)
    context = {
        "product": detail,
        "seo": detail["seo"],
    }
    return engine.render_page(request, "product", context)


def storefront_cart(request):
    return engine.render_page(request, "cart")


def storefront_checkout(request):
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return _login_redirect(request)
    return engine.render_page(request, "checkout")


def storefront_order_success(request):
    return engine.render_page(request, "order_success")


def storefront_dashboard(request):
    return engine.render_page(request, "dashboard")


def storefront_profile(request):
    return engine.render_page(request, "profile")


def storefront_profile_edit(request):
    return engine.render_page(request, "profile_edit")


def storefront_wishlist(request):
    return engine.render_page(request, "wishlist")


def storefront_orders(request):
    return engine.render_page(request, "orders")


def storefront_order_detail(request, order_id):
    return engine.render_page(request, "order_detail", {"order_id": order_id})


def storefront_invoices(request):
    return engine.render_page(request, "invoices")


def storefront_comments(request):
    return engine.render_page(request, "comments")


def storefront_addresses(request):
    return engine.render_page(request, "addresses")


def storefront_blog_list(request):
    return engine.render_page(request, "blog_list")


def storefront_blog_single(request, slug):
    return engine.render_page(request, "blog_single", {"blog_slug": slug})


def storefront_login(request):
    return engine.render_page(request, "auth", {"auth_mode": "login"})


def storefront_register(request):
    return engine.render_page(request, "auth", {"auth_mode": "register"})


def storefront_downloads(request):
    return engine.render_page(request, "downloads")


def storefront_subscriptions(request):
    return engine.render_page(request, "subscriptions")


def storefront_404(request, exception=None):
    return engine.render_page(request, "404", status=404)


def storefront_500(request):
    return engine.render_page(request, "500", status=500)
