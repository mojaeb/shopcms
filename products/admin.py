"""Products admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from products.models import (
    Brand,
    Category,
    Inventory,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
    ProductVideo,
    Tag,
)


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ("name", "store", "status", "base_price", "category", "is_featured")
    list_filter = ("store", "status", "product_type", "is_featured")
    search_fields = ("name", "slug", "sku")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVariantInline]


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "store", "parent", "is_active", "sort_order")
    list_filter = ("store", "is_active")


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ("name", "store", "is_active")
    list_filter = ("store",)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "store", "slug")
    list_filter = ("store",)


@admin.register(ProductAttribute)
class ProductAttributeAdmin(ModelAdmin):
    list_display = ("name", "store", "display_type")
    list_filter = ("store",)


@admin.register(Inventory)
class InventoryAdmin(ModelAdmin):
    list_display = ("product", "variant", "quantity", "reserved", "track_inventory")
    list_filter = ("track_inventory",)
