"""Product search and filter service."""

from django.db.models import F, Max, Min, Prefetch, Q

from core.cache import cache_manager
from core.cache.keys import product_filter_options
from products.enums import ProductSortOrder, ProductStatus, ProductType
from products.models import Brand, Category, Product, ProductAttribute, ProductVariant


class ProductSearchService:
    """Advanced product search, filter, and sort."""

    SORT_FIELDS = {
        ProductSortOrder.NEWEST: ["-is_featured", "-created_at"],
        ProductSortOrder.OLDEST: ["created_at"],
        ProductSortOrder.PRICE_ASC: ["base_price"],
        ProductSortOrder.PRICE_DESC: ["-base_price"],
        ProductSortOrder.NAME_ASC: ["name"],
        ProductSortOrder.NAME_DESC: ["-name"],
        ProductSortOrder.FEATURED: ["-is_featured", "-created_at"],
    }

    def search(
        self,
        store,
        search: str = "",
        category_slug: str | None = None,
        brand_slug: str | None = None,
        brand_slugs: list[str] | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        attributes: dict[str, str] | None = None,
        tag_slug: str | None = None,
        in_stock: bool | None = None,
        featured: bool | None = None,
        status: str | None = ProductStatus.ACTIVE,
        sort: str = ProductSortOrder.NEWEST,
    ):
        qs = self._base_queryset(store)
        qs = self._apply_filters(
            qs,
            search=search,
            category_slug=category_slug,
            brand_slug=brand_slug,
            brand_slugs=brand_slugs,
            min_price=min_price,
            max_price=max_price,
            attributes=attributes,
            tag_slug=tag_slug,
            in_stock=in_stock,
            featured=featured,
            status=status,
        )
        return self._apply_sort(qs, sort)

    def get_filter_options(self, store, category_slug: str | None = None) -> dict:
        cache_key = product_filter_options(store.id, category_slug)
        return cache_manager.get_or_set(
            cache_key,
            lambda: self._build_filter_options(store, category_slug),
            ttl="products",
        )

    def _build_filter_options(self, store, category_slug: str | None = None) -> dict:
        base_qs = Product.objects.filter(store=store, status=ProductStatus.ACTIVE)
        if category_slug:
            base_qs = base_qs.filter(category__slug=category_slug)

        price_agg = base_qs.aggregate(min_price=Min("base_price"), max_price=Max("base_price"))
        categories = Category.objects.filter(store=store, is_active=True).order_by("sort_order", "name")
        brands = Brand.objects.filter(
            store=store,
            is_active=True,
            products__status=ProductStatus.ACTIVE,
        ).distinct().order_by("name")

        attrs = ProductAttribute.objects.filter(store=store).prefetch_related("values").order_by("sort_order")
        attributes = []
        for attr in attrs:
            values = [
                {
                    "id": v.id,
                    "value": v.value,
                    "slug": v.slug,
                    "color_code": v.color_code,
                    "icon": v.icon,
                }
                for v in attr.values.all()
            ]
            if values:
                attributes.append({
                    "id": attr.id,
                    "name": attr.name,
                    "slug": attr.slug,
                    "display_type": attr.display_type,
                    "button_style": attr.button_style or None,
                    "values": values,
                })

        return {
            "categories": [{"id": c.id, "name": c.name, "slug": c.slug} for c in categories],
            "brands": [{"id": b.id, "name": b.name, "slug": b.slug} for b in brands],
            "attributes": attributes,
            "price_range": {
                "min": int(price_agg["min_price"] or 0),
                "max": int(price_agg["max_price"] or 0),
            },
            "sort_options": [
                {"value": choice.value, "label": choice.label}
                for choice in ProductSortOrder
            ],
        }

    @staticmethod
    def parse_attributes(raw: str | None) -> dict[str, str]:
        if not raw:
            return {}
        result = {}
        for part in raw.split(","):
            part = part.strip()
            if ":" not in part:
                continue
            attr_slug, value_slug = part.split(":", 1)
            if attr_slug and value_slug:
                result[attr_slug.strip()] = value_slug.strip()
        return result

    @staticmethod
    def parse_brand_list(brand: str | None = None, brands: str | None = None) -> list[str]:
        slugs = []
        if brand:
            slugs.append(brand)
        if brands:
            slugs.extend(s.strip() for s in brands.split(",") if s.strip())
        return list(dict.fromkeys(slugs))

    def _base_queryset(self, store):
        return Product.objects.filter(store=store).select_related("category", "brand").prefetch_related(
            "images",
            "tags",
            Prefetch("variants", queryset=ProductVariant.objects.filter(is_active=True)),
        )

    def _apply_filters(
        self,
        qs,
        search: str = "",
        category_slug: str | None = None,
        brand_slug: str | None = None,
        brand_slugs: list[str] | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        attributes: dict[str, str] | None = None,
        tag_slug: str | None = None,
        in_stock: bool | None = None,
        featured: bool | None = None,
        status: str | None = ProductStatus.ACTIVE,
    ):
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(short_description__icontains=search)
                | Q(description__icontains=search)
                | Q(sku__icontains=search)
                | Q(tags__name__icontains=search)
            )
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        slugs = brand_slugs or []
        if brand_slug and brand_slug not in slugs:
            slugs = [brand_slug, *slugs]
        if slugs:
            qs = qs.filter(brand__slug__in=slugs)
        if min_price is not None:
            qs = qs.filter(base_price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(base_price__lte=max_price)
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)
        if featured is not None:
            qs = qs.filter(is_featured=featured)
        if attributes:
            for attr_slug, value_slug in attributes.items():
                qs = qs.filter(
                    variants__is_active=True,
                    variants__attributes__slug=value_slug,
                    variants__attributes__attribute__slug=attr_slug,
                )
            qs = qs.distinct()
        if in_stock is True:
            qs = qs.filter(self._in_stock_q()).distinct()
        elif in_stock is False:
            qs = qs.exclude(self._in_stock_q()).distinct()
        return qs

    def _in_stock_q(self):
        return (
            Q(inventory_items__track_inventory=False)
            | Q(inventory_items__quantity__gt=F("inventory_items__reserved"))
            | Q(
                product_type=ProductType.VARIABLE,
                variants__is_active=True,
                variants__inventory__quantity__gt=F("variants__inventory__reserved"),
            )
        )

    def _apply_sort(self, qs, sort: str):
        sort_key = sort if sort in self.SORT_FIELDS else ProductSortOrder.NEWEST
        return qs.order_by(*self.SORT_FIELDS[sort_key])
