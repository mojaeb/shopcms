"""Store admin products API."""

from django.core.exceptions import ValidationError

from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.pagination import PageNumberPagination, paginate

from dashboard.authentication_store import store_products_auth
from products.api.public import ProductListSchema
from products.enums import ProductStatus, ProductType
from products.models import Brand, Category, Product, ProductAttribute
from products.services.product import ProductService
from tenants.context import get_current_store

router = Router(auth=store_products_auth)
service = ProductService()


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


class ProductImageInput(Schema):
    image: str
    alt_text: str = ""
    is_primary: bool = False
    sort_order: int = 0


class ProductVariantInput(Schema):
    id: int | None = None
    sku: str = ""
    price: float = 0
    compare_price: float | None = None
    attribute_value_ids: list[int] = []
    stock: int = 0
    is_active: bool = True


class ProductCreateSchema(Schema):
    name: str
    slug: str
    description: str = ""
    short_description: str = ""
    product_type: str = ProductType.SIMPLE
    status: str = ProductStatus.DRAFT
    base_price: float = 0
    compare_price: float | None = None
    sku: str = ""
    category_id: int | None = None
    brand_id: int | None = None
    is_featured: bool = False
    initial_stock: int = 0
    stock: int | None = None
    tags: list[str] = []
    images: list[ProductImageInput] = []
    variants: list[ProductVariantInput] = []
    meta_title: str = ""
    meta_description: str = ""
    meta_keywords: str = ""
    og_image: str = ""


class ProductUpdateSchema(Schema):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    short_description: str | None = None
    product_type: str | None = None
    status: str | None = None
    base_price: float | None = None
    compare_price: float | None = None
    sku: str | None = None
    category_id: int | None = None
    brand_id: int | None = None
    is_featured: bool | None = None
    initial_stock: int | None = None
    stock: int | None = None
    tags: list[str] | None = None
    images: list[ProductImageInput] | None = None
    variants: list[ProductVariantInput] | None = None
    meta_title: str | None = None
    meta_description: str | None = None
    meta_keywords: str | None = None
    og_image: str | None = None


class CategoryCreateSchema(Schema):
    name: str
    slug: str
    parent_id: int | None = None
    description: str = ""


class BrandCreateSchema(Schema):
    name: str
    slug: str
    logo: str = ""


class AttributeValueInput(Schema):
    value: str
    slug: str = ""
    color_code: str = ""
    icon: str = ""
    sort_order: int = 0


class AttributeCreateSchema(Schema):
    name: str
    slug: str = ""
    display_type: str = "select"
    button_style: str = ""
    sort_order: int = 0
    values: list[AttributeValueInput] = []


class AttributeValuesAddSchema(Schema):
    values: list[AttributeValueInput]


def _attr_payload(attr: ProductAttribute) -> dict:
    return {
        "id": attr.id,
        "name": attr.name,
        "slug": attr.slug,
        "display_type": attr.display_type,
        "button_style": attr.button_style or None,
        "values": [
            {
                "id": v.id,
                "value": v.value,
                "slug": v.slug,
                "color_code": v.color_code,
                "icon": v.icon,
            }
            for v in attr.values.all()
        ],
    }


@router.get("/categories/list")
def list_categories(request):
    store = _store(request)
    cats = Category.objects.filter(store=store).order_by("sort_order")
    return [{"id": c.id, "name": c.name, "slug": c.slug, "parent_id": c.parent_id} for c in cats]


@router.post("/categories")
def create_category(request, payload: CategoryCreateSchema):
    store = _store(request)
    parent = None
    if payload.parent_id:
        parent = Category.objects.get(pk=payload.parent_id, store=store)
    cat = Category.objects.create(
        store=store,
        parent=parent,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
    )
    return {"id": cat.id, "slug": cat.slug}


@router.get("/brands/list")
def list_brands(request):
    store = _store(request)
    return [{"id": b.id, "name": b.name, "slug": b.slug} for b in Brand.objects.filter(store=store)]


@router.post("/brands")
def create_brand(request, payload: BrandCreateSchema):
    store = _store(request)
    brand = Brand.objects.create(store=store, name=payload.name, slug=payload.slug, logo=payload.logo)
    return {"id": brand.id, "slug": brand.slug}


@router.get("/attributes/list")
def list_attributes(request):
    store = _store(request)
    attrs = ProductAttribute.objects.filter(store=store).prefetch_related("values")
    return [_attr_payload(a) for a in attrs]


@router.post("/attributes")
def create_attribute(request, payload: AttributeCreateSchema):
    store = _store(request)
    attr = service.create_attribute(store, payload.dict())
    attr = ProductAttribute.objects.prefetch_related("values").get(pk=attr.id)
    return _attr_payload(attr)


@router.post("/attributes/{attribute_id}/values")
def add_attribute_values(request, attribute_id: int, payload: AttributeValuesAddSchema):
    store = _store(request)
    try:
        attr = ProductAttribute.objects.get(pk=attribute_id, store=store)
    except ProductAttribute.DoesNotExist:
        raise HttpError(404, "ویژگی یافت نشد")
    service.add_attribute_values(attr, [v.dict() for v in payload.values])
    attr = ProductAttribute.objects.prefetch_related("values").get(pk=attr.id)
    return _attr_payload(attr)


@router.get("/", response=list[ProductListSchema])
@paginate(PageNumberPagination, page_size=20)
def list_products_admin(request, search: str = "", status: str | None = None):
    store = _store(request)
    return [
        service.serialize_product_list(p)
        for p in service.list_products(store, search=search, status=status or None)
    ]


@router.post("/")
def create_product(request, payload: ProductCreateSchema):
    store = _store(request)
    try:
        product = service.create_product(store, payload.dict())
    except ValidationError as exc:
        raise HttpError(400, exc.messages[0] if exc.messages else str(exc))
    return service.serialize_product_detail(product, for_admin=True)


@router.get("/{product_id}")
def get_product(request, product_id: int):
    store = _store(request)
    product = service.get_product_by_id(store, product_id)
    if not product:
        raise HttpError(404, "محصول یافت نشد")
    return service.serialize_product_detail(product, for_admin=True)


@router.put("/{product_id}")
def update_product(request, product_id: int, payload: ProductUpdateSchema):
    store = _store(request)
    product = service.get_product_by_id(store, product_id)
    if not product:
        raise HttpError(404, "محصول یافت نشد")
    raw = payload.dict(exclude_unset=True)
    try:
        product = service.update_product(product, raw)
    except ValidationError as exc:
        raise HttpError(400, exc.messages[0] if exc.messages else str(exc))
    return service.serialize_product_detail(product, for_admin=True)


@router.delete("/{product_id}")
def delete_product(request, product_id: int):
    store = _store(request)
    try:
        product = Product.objects.get(pk=product_id, store=store)
        product.delete()
        return {"detail": "محصول حذف شد"}
    except Product.DoesNotExist:
        raise HttpError(404, "محصول یافت نشد")
