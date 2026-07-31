"""Product service layer."""

from django.db import transaction
from django.utils.text import slugify

from products.enums import ProductStatus, ProductType
from products.models import (
    Brand,
    Category,
    Inventory,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
    Tag,
)
from products.services.search import ProductSearchService
from cms.services.shortcodes import expand_shortcodes
from products.utils import normalize_color_code, parse_color_codes

PRODUCT_SCALAR_FIELDS = {
    "name",
    "slug",
    "description",
    "short_description",
    "product_type",
    "status",
    "base_price",
    "compare_price",
    "sku",
    "is_featured",
    "meta_title",
    "meta_description",
    "meta_keywords",
    "og_image",
    "canonical_url",
    "robots",
}


class ProductService:
    """Business logic for products."""

    def __init__(self):
        self.search_service = ProductSearchService()

    def list_products(
        self,
        store,
        search: str = "",
        category_slug: str | None = None,
        brand_slug: str | None = None,
        status: str | None = ProductStatus.ACTIVE,
        featured: bool | None = None,
        **kwargs,
    ):
        return self.search_service.search(
            store,
            search=search,
            category_slug=category_slug,
            brand_slug=brand_slug,
            status=status,
            featured=featured,
            **kwargs,
        )

    def get_product(self, store, slug: str, active_only: bool = True) -> Product | None:
        qs = Product.objects.filter(store=store, slug=slug).select_related("category", "brand").prefetch_related(
            "images",
            "videos",
            "tags",
            "variants__attributes",
            "variants__attributes__attribute",
            "variants__inventory",
            "inventory_items",
        )
        if active_only:
            qs = qs.filter(status=ProductStatus.ACTIVE)
        return qs.first()

    def get_product_by_id(self, store, product_id: int) -> Product | None:
        return (
            Product.objects.filter(pk=product_id, store=store)
            .select_related("category", "brand")
            .prefetch_related(
                "images",
                "videos",
                "tags",
                "variants__attributes__attribute",
                "variants__inventory",
                "inventory_items",
            )
            .first()
        )

    def serialize_product_list(self, product: Product) -> dict:
        inv = self._get_product_inventory(product)
        compare = product.compare_price
        base = product.base_price
        discount_percent = None
        if compare is not None and base is not None and compare > base:
            # Percent off the compare (list) price; only surface meaningful discounts.
            pct = int(((compare - base) / compare) * 100)
            if pct >= 5:
                discount_percent = pct
        return {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "short_description": product.short_description,
            "base_price": str(product.base_price),
            "compare_price": str(product.compare_price) if product.compare_price else None,
            "discount_percent": discount_percent,
            "image": product.primary_image,
            "category": product.category.name if product.category else None,
            "category_slug": product.category.slug if product.category else None,
            "category_id": product.category_id,
            "brand": product.brand.name if product.brand else None,
            "brand_id": product.brand_id,
            "product_type": product.product_type,
            "is_featured": product.is_featured,
            "status": product.status,
            "in_stock": inv["in_stock"],
            "available": inv["available"],
        }

    def serialize_product_detail(self, product: Product, *, for_admin: bool = False) -> dict:
        inv = self._get_product_inventory(product)
        variants_qs = product.variants.all() if for_admin else product.variants.filter(is_active=True)
        description = product.description or ""
        if not for_admin:
            description = expand_shortcodes(description, product.store)
        detail = {
            **self.serialize_product_list(product),
            "description": description,
            "sku": product.sku,
            "images": [
                {
                    "id": i.id,
                    "image": i.image,
                    "alt_text": i.alt_text,
                    "is_primary": i.is_primary,
                    "sort_order": i.sort_order,
                }
                for i in product.images.all()
            ],
            "videos": [{"id": v.id, "url": v.url, "title": v.title} for v in product.videos.all()],
            "tags": [t.name for t in product.tags.all()],
            "tag_slugs": [t.slug for t in product.tags.all()],
            "variants": [self.serialize_variant(v, for_admin=for_admin) for v in variants_qs],
            "attribute_options": self._build_attribute_options(product, for_admin=for_admin),
            "inventory": inv,
            "seo": {
                "meta_title": product.meta_title,
                "meta_description": product.meta_description,
                "meta_keywords": product.meta_keywords,
                "og_image": product.og_image or product.primary_image,
            },
            "meta_title": product.meta_title,
            "meta_description": product.meta_description,
            "meta_keywords": product.meta_keywords,
            "og_image": product.og_image,
        }
        if for_admin and product.product_type == ProductType.SIMPLE:
            simple_inv = product.inventory_items.filter(variant__isnull=True).first()
            detail["stock"] = simple_inv.quantity if simple_inv else 0
        return detail

    def serialize_variant(self, variant: ProductVariant, *, for_admin: bool = False) -> dict:
        inv = getattr(variant, "inventory", None)
        data = {
            "id": variant.id,
            "sku": variant.sku,
            "price": str(variant.price),
            "compare_price": str(variant.compare_price) if variant.compare_price else None,
            "attributes": [
                self._serialize_variant_attribute(av)
                for av in variant.attributes.select_related("attribute").all()
            ],
            "in_stock": inv.is_in_stock if inv else True,
            "available": inv.available if inv else 0,
            "is_active": variant.is_active,
        }
        if for_admin:
            data["attribute_value_ids"] = list(variant.attributes.values_list("id", flat=True))
            data["stock"] = inv.quantity if inv else 0
        return data

    def _serialize_variant_attribute(self, av: ProductAttributeValue) -> dict:
        codes = parse_color_codes(av.color_code)
        return {
            "id": av.id,
            "attribute_id": av.attribute_id,
            "name": av.attribute.name,
            "slug": av.attribute.slug,
            "display_type": av.attribute.display_type,
            "button_style": av.attribute.button_style or None,
            "value": av.value,
            "value_slug": av.slug,
            "color_code": codes[0] if codes else (av.color_code or ""),
            "color_codes": codes,
            "icon": av.icon,
        }

    def _serialize_attribute_value(self, av: ProductAttributeValue) -> dict:
        codes = parse_color_codes(av.color_code)
        return {
            "id": av.id,
            "value": av.value,
            "slug": av.slug,
            "color_code": codes[0] if codes else (av.color_code or ""),
            "color_codes": codes,
            "icon": av.icon,
        }

    def _serialize_attribute_option(self, attr: ProductAttribute, values: list[ProductAttributeValue]) -> dict:
        return {
            "id": attr.id,
            "name": attr.name,
            "slug": attr.slug,
            "display_type": attr.display_type,
            "button_style": attr.button_style or None,
            "values": [self._serialize_attribute_value(v) for v in values],
        }

    def _build_attribute_options(self, product: Product, *, for_admin: bool = False) -> list[dict]:
        variants_qs = product.variants.all() if for_admin else product.variants.filter(is_active=True)
        value_ids: set[int] = set()
        for variant in variants_qs:
            value_ids.update(variant.attributes.values_list("id", flat=True))
        if not value_ids:
            return []

        values = (
            ProductAttributeValue.objects.filter(id__in=value_ids)
            .select_related("attribute")
            .order_by("attribute__sort_order", "attribute__name", "sort_order", "value")
        )
        grouped: dict[int, dict] = {}
        for av in values:
            attr = av.attribute
            bucket = grouped.setdefault(
                attr.id,
                {"attr": attr, "values": []},
            )
            bucket["values"].append(av)
        return [
            self._serialize_attribute_option(item["attr"], item["values"])
            for item in sorted(grouped.values(), key=lambda row: (row["attr"].sort_order, row["attr"].name))
        ]

    def _get_product_inventory(self, product: Product) -> dict:
        if product.product_type == ProductType.VARIABLE:
            total = 0
            in_stock = False
            for v in product.variants.filter(is_active=True):
                inv = getattr(v, "inventory", None)
                if inv:
                    total += inv.available
                    if inv.is_in_stock:
                        in_stock = True
            return {"available": total, "in_stock": in_stock, "track_inventory": True}

        inv = product.inventory_items.filter(variant__isnull=True).first()
        if inv:
            return {
                "available": inv.available,
                "in_stock": inv.is_in_stock,
                "track_inventory": inv.track_inventory,
            }
        return {"available": 0, "in_stock": True, "track_inventory": False}

    def list_categories(self, store, parent=None):
        return Category.objects.filter(store=store, parent=parent, is_active=True).order_by("sort_order")

    def list_brands(self, store):
        return Brand.objects.filter(store=store, is_active=True).order_by("name")

    def _extract_product_fields(self, data: dict) -> dict:
        fields = {}
        for key in PRODUCT_SCALAR_FIELDS:
            if key in data:
                fields[key] = data[key]
        if "category_id" in data:
            fields["category_id"] = data["category_id"]
        if "brand_id" in data:
            fields["brand_id"] = data["brand_id"]
        return fields

    def _sync_tags(self, store, product: Product, tag_names_or_slugs: list | None):
        if tag_names_or_slugs is None:
            return
        tags = []
        for raw in tag_names_or_slugs:
            raw = (raw or "").strip()
            if not raw:
                continue
            slug = slugify(raw, allow_unicode=True) or raw
            tag, _ = Tag.objects.get_or_create(
                store=store,
                slug=slug,
                defaults={"name": raw},
            )
            tags.append(tag)
        product.tags.set(tags)

    def _sync_images(self, product: Product, images: list | None):
        if images is None:
            return
        product.images.all().delete()
        for idx, img in enumerate(images):
            if not isinstance(img, dict):
                continue
            url = (img.get("image") or "").strip()
            if not url:
                continue
            ProductImage.objects.create(
                product=product,
                image=url,
                alt_text=img.get("alt_text") or "",
                sort_order=img.get("sort_order", idx),
                is_primary=bool(img.get("is_primary")) or idx == 0,
            )

    def _validate_variant_attribute_values(self, product: Product, value_ids: list[int]) -> None:
        if not value_ids:
            return
        values = list(
            ProductAttributeValue.objects.filter(
                pk__in=value_ids,
                attribute__store=product.store,
            ).select_related("attribute")
        )
        if len(values) != len(set(value_ids)):
            from django.core.exceptions import ValidationError

            raise ValidationError("برخی مقادیر ویژگی نامعتبر هستند.")
        seen_attrs: set[int] = set()
        for av in values:
            if av.attribute_id in seen_attrs:
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    f"برای هر نوع variant فقط یک مقدار مجاز است (تکرار: {av.attribute.name})."
                )
            seen_attrs.add(av.attribute_id)

    def _sync_variants(self, product: Product, variants: list | None):
        if variants is None:
            return
        keep_ids = []
        for v_data in variants:
            if not isinstance(v_data, dict):
                continue
            attrs = v_data.get("attribute_value_ids") or []
            stock = int(v_data.get("stock") or 0)
            variant_id = v_data.get("id")
            self._validate_variant_attribute_values(product, [int(x) for x in attrs if x])
            payload = {
                "sku": v_data.get("sku") or "",
                "price": v_data.get("price") if v_data.get("price") is not None else product.base_price,
                "compare_price": v_data.get("compare_price"),
                "is_active": v_data.get("is_active", True),
            }
            if variant_id:
                try:
                    variant = product.variants.get(pk=variant_id)
                except ProductVariant.DoesNotExist:
                    variant = ProductVariant.objects.create(product=product, **payload)
                else:
                    for field, value in payload.items():
                        setattr(variant, field, value)
                    variant.save()
            else:
                variant = ProductVariant.objects.create(product=product, **payload)

            if attrs:
                variant.attributes.set(
                    ProductAttributeValue.objects.filter(
                        pk__in=attrs,
                        attribute__store=product.store,
                    )
                )
            else:
                variant.attributes.clear()

            inv, _ = Inventory.objects.get_or_create(
                variant=variant,
                defaults={"product": product, "quantity": stock},
            )
            if inv.quantity != stock or inv.product_id != product.id:
                inv.product = product
                inv.quantity = stock
                inv.save(update_fields=["product", "quantity", "updated_at"])

            keep_ids.append(variant.id)

        product.variants.exclude(pk__in=keep_ids).delete()
        product.inventory_items.filter(variant__isnull=True).delete()

    @transaction.atomic
    def create_product(self, store, data: dict) -> Product:
        data = dict(data)
        tag_input = data.pop("tags", None)
        if tag_input is None:
            tag_input = data.pop("tag_slugs", None)
        images = data.pop("images", None)
        variants = data.pop("variants", None)
        initial_stock = int(data.pop("initial_stock", data.pop("stock", 0)) or 0)

        fields = self._extract_product_fields(data)
        product = Product.objects.create(store=store, **fields)

        self._sync_tags(store, product, tag_input)
        self._sync_images(product, images or [])

        if product.product_type == ProductType.VARIABLE:
            self._sync_variants(product, variants or [])
        else:
            Inventory.objects.create(product=product, quantity=initial_stock)

        return self.get_product_by_id(store, product.id) or product

    @transaction.atomic
    def update_product(self, product: Product, data: dict) -> Product:
        data = dict(data)
        store = product.store
        tag_input = data.pop("tags", None)
        if "tag_slugs" in data and tag_input is None:
            tag_input = data.pop("tag_slugs")
        images = data.pop("images", None)
        variants = data.pop("variants", None)
        stock = data.pop("initial_stock", data.pop("stock", None))

        fields = self._extract_product_fields(data)
        for field, value in fields.items():
            setattr(product, field, value)
        product.save()

        if tag_input is not None:
            self._sync_tags(store, product, tag_input)
        if images is not None:
            self._sync_images(product, images)

        if product.product_type == ProductType.VARIABLE:
            if variants is not None:
                self._sync_variants(product, variants)
        else:
            product.variants.all().delete()
            if stock is not None:
                self.update_inventory(product=product, quantity=int(stock))

        return self.get_product_by_id(store, product.id) or product

    @transaction.atomic
    def create_attribute(self, store, data: dict) -> ProductAttribute:
        values = data.pop("values", []) or []
        attr = ProductAttribute.objects.create(
            store=store,
            name=data["name"],
            slug=data.get("slug") or slugify(data["name"], allow_unicode=True),
            display_type=data.get("display_type") or "select",
            button_style=data.get("button_style") or "",
            sort_order=int(data.get("sort_order") or 0),
        )
        for idx, raw in enumerate(values):
            if isinstance(raw, str):
                raw = {"value": raw}
            value = (raw.get("value") or "").strip()
            if not value:
                continue
            ProductAttributeValue.objects.create(
                attribute=attr,
                value=value,
                slug=raw.get("slug") or slugify(value, allow_unicode=True) or f"v-{idx}",
                color_code=normalize_color_code(raw.get("color_code") or ""),
                icon=raw.get("icon") or "",
                sort_order=int(raw.get("sort_order") or idx),
            )
        return attr

    @transaction.atomic
    def add_attribute_values(self, attribute: ProductAttribute, values: list) -> ProductAttribute:
        for idx, raw in enumerate(values or []):
            if isinstance(raw, str):
                raw = {"value": raw}
            value = (raw.get("value") or "").strip()
            if not value:
                continue
            slug = raw.get("slug") or slugify(value, allow_unicode=True) or f"v-{idx}"
            ProductAttributeValue.objects.get_or_create(
                attribute=attribute,
                slug=slug,
                defaults={
                    "value": value,
                    "color_code": normalize_color_code(raw.get("color_code") or ""),
                    "icon": raw.get("icon") or "",
                    "sort_order": int(raw.get("sort_order") or idx),
                },
            )
        return attribute

    @transaction.atomic
    def update_inventory(
        self,
        product: Product | None = None,
        variant: ProductVariant | None = None,
        quantity: int = 0,
    ):
        if variant:
            inv, _ = Inventory.objects.get_or_create(
                variant=variant, defaults={"product": variant.product}
            )
            inv.quantity = quantity
            inv.save(update_fields=["quantity", "updated_at"])
            return inv
        if product:
            inv, _ = Inventory.objects.get_or_create(product=product, variant=None)
            inv.quantity = quantity
            inv.save(update_fields=["quantity", "updated_at"])
            return inv
