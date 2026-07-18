"""Storefront views with theme engine."""

from django.http import Http404

from tenants.context import get_current_store
from tenants.theme.engine import ThemeEngine

engine = ThemeEngine()


def _require_store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store and not request.GET.get("preview"):
        raise Http404("فروشگاه یافت نشد")
    return store


def storefront_home(request):
    store = _require_store(request)
    extra = {}
    if store:
        from cms.services.cms import CMSService
        from products.services.product import ProductService

        extra = CMSService().get_storefront_context(store)
        ps = ProductService()
        categories = list(ps.list_categories(store)[:8])
        products = list(ps.list_products(store, featured=True)[:8])
        if len(products) < 4:
            products = list(ps.list_products(store)[:8])
        extra["home_categories"] = [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "image": getattr(c, "image", "") or "",
            }
            for c in categories
        ]
        extra["home_products"] = [ps.serialize_product_list(p) for p in products]
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
        "categories": [{"name": c.name, "slug": c.slug} for c in categories],
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
