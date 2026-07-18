"""Route order: specific paths before slug."""

from ninja import Router, Schema
from ninja.pagination import PageNumberPagination, paginate

from products.enums import ProductSortOrder
from products.models import Category
from products.services.product import ProductService
from products.services.search import ProductSearchService
from tenants.context import get_current_store

router = Router()
service = ProductService()
search_service = ProductSearchService()


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


@router.get("/", response=list[ProductListSchema])
@paginate(PageNumberPagination, page_size=20)
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
):
    store = _get_store(request)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    brand_slugs = search_service.parse_brand_list(brand, brands)
    attr_map = search_service.parse_attributes(attributes)
    products = service.list_products(
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
    return [service.serialize_product_list(p) for p in products]


@router.get("/{slug}")
def product_detail(request, slug: str):
    store = _get_store(request)
    if not store:
        return 404, {"detail": "فروشگاه یافت نشد"}
    product = service.get_product(store, slug)
    if not product:
        return 404, {"detail": "محصول یافت نشد"}
    return service.serialize_product_detail(product)
