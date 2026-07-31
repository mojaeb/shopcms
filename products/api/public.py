"""Route order: specific paths before slug."""

from ninja import Router, Schema

from core.cache import cache_manager
from core.cache.keys import product_detail, product_list
from products.enums import ProductSortOrder
from products.models import Category
from products.services.product import ProductService
from products.services.search import ProductSearchService
from tenants.context import get_current_store

router = Router()
service = ProductService()
search_service = ProductSearchService()

PRODUCT_PAGE_SIZE = 20
PRODUCT_MAX_PAGE_SIZE = 100


class ProductListSchema(Schema):
    id: int
    name: str
    slug: str
    short_description: str
    base_price: str
    compare_price: str | None = None
    image: str
    category: str | None = None
    category_id: int | None = None
    brand: str | None = None
    brand_id: int | None = None
    product_type: str = "simple"
    is_featured: bool
    status: str = "active"
    in_stock: bool
    available: int


def _get_store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        return None
    return store


def _clamp_page(page: int, page_size: int) -> tuple[int, int]:
    page = max(1, page or 1)
    page_size = min(max(page_size or PRODUCT_PAGE_SIZE, 1), PRODUCT_MAX_PAGE_SIZE)
    return page, page_size


@router.get("/filters")
def get_filters(request, category: str | None = None):
    store = _get_store(request)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    return search_service.get_filter_options(store, category_slug=category)


@router.get("/categories/list")
def list_categories(request, parent: str | None = None):
    store = _get_store(request)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    parent_cat = Category.objects.filter(store=store, slug=parent).first() if parent else None
    cats = service.list_categories(store, parent_cat)
    return [{"id": c.id, "name": c.name, "slug": c.slug, "image": c.image} for c in cats]


@router.get("/brands/list")
def list_brands(request):
    store = _get_store(request)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    brands = service.list_brands(store)
    return [{"id": b.id, "name": b.name, "slug": b.slug, "logo": b.logo} for b in brands]


@router.get("/", response={200: dict})
def list_products(
    request,
    search: str = "",
    category: str | None = None,
    brand: str | None = None,
    brands: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    attributes: str | None = None,
    tag: str | None = None,
    in_stock: bool | None = None,
    featured: bool | None = None,
    sort: str = ProductSortOrder.NEWEST,
    page: int = 1,
    page_size: int = PRODUCT_PAGE_SIZE,
):
    store = _get_store(request)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}

    page, page_size = _clamp_page(page, page_size)
    brand_slugs = search_service.parse_brand_list(brand, brands)
    attr_map = search_service.parse_attributes(attributes)
    params = {
        "search": search,
        "category": category,
        "brand_slugs": brand_slugs,
        "min_price": min_price,
        "max_price": max_price,
        "attributes": attr_map,
        "tag": tag,
        "in_stock": in_stock,
        "featured": featured,
        "sort": sort,
        "page": page,
        "page_size": page_size,
    }
    cache_key = product_list(store.id, cache_manager.hash_params(params))

    def factory():
        qs = service.list_products(
            store,
            search=search,
            category_slug=category,
            brand_slugs=brand_slugs or None,
            min_price=min_price,
            max_price=max_price,
            attributes=attr_map or None,
            tag_slug=tag,
            in_stock=in_stock,
            featured=featured,
            sort=sort,
        )
        count = qs.count()
        offset = (page - 1) * page_size
        items = [service.serialize_product_list(p) for p in qs[offset : offset + page_size]]
        return {"items": items, "count": count}

    return cache_manager.get_or_set(cache_key, factory, ttl="products")


@router.get("/{slug}")
def product_detail_view(request, slug: str):
    store = _get_store(request)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}

    cache_key = product_detail(store.id, slug)
    cached = cache_manager.get(cache_key)
    if cached is not None:
        if cached == "__missing__":
            return 404, {"detail": "محصول یافت نشد"}
        return cached

    product = service.get_product(store, slug)
    if not product:
        cache_manager.set(cache_key, "__missing__", ttl="short")
        return 404, {"detail": "محصول یافت نشد"}

    payload = service.serialize_product_detail(product)
    cache_manager.set(cache_key, payload, ttl="products")
    return payload
