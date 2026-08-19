"""Shipping admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from shipping.models import ShippingMethod, ShippingPrice, ShippingRule, ShippingZone


class ShippingPriceInline(TabularInline):
    model = ShippingPrice
    extra = 0
    fields = (
        "from_city",
        "to_city",
        "zone_tier",
        "weight_min_kg",
        "weight_max_kg",
        "price",
        "extra_per_kg",
    )


class ShippingRuleInline(TabularInline):
    model = ShippingRule
    extra = 0


@admin.register(ShippingZone)
class ShippingZoneAdmin(ModelAdmin):
    list_display = ("name", "store", "is_active")
    list_filter = ("store", "is_active")
    search_fields = ("name", "store__name")


@admin.register(ShippingMethod)
class ShippingMethodAdmin(ModelAdmin):
    list_display = (
        "name",
        "store",
        "provider",
        "calculation_mode",
        "payment_type",
        "is_active",
        "sort_order",
    )
    list_filter = ("store", "provider", "calculation_mode", "payment_type", "is_active")
    search_fields = ("name", "slug")
    inlines = [ShippingPriceInline, ShippingRuleInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "store",
                    "zone",
                    ("name", "slug"),
                    ("provider", "calculation_mode", "payment_type"),
                    ("is_active", "sort_order", "estimated_days"),
                    ("min_order_amount", "free_shipping_threshold"),
                ),
            },
        ),
        (
            "تنظیمات config",
            {
                "description": (
                    "کلیدهای رایج: fixed_price، origin_city، "
                    "extra_cost_flat، extra_cost_percent؛ "
                    "برای پیک: delivery_cities (لیست شهرها)؛ "
                    "برای پست: max_weight_kg."
                ),
                "fields": ("config",),
            },
        ),
    )


@admin.register(ShippingPrice)
class ShippingPriceAdmin(ModelAdmin):
    list_display = (
        "method",
        "from_city",
        "to_city",
        "zone_tier",
        "weight_min_kg",
        "weight_max_kg",
        "price",
    )
    list_filter = ("method__store", "method", "zone_tier")
    fields = (
        "method",
        ("from_city", "to_city", "zone_tier"),
        ("weight_min_kg", "weight_max_kg"),
        ("price", "extra_per_kg"),
    )


@admin.register(ShippingRule)
class ShippingRuleAdmin(ModelAdmin):
    list_display = ("name", "method", "zone", "priority", "is_active")
    list_filter = ("method__store", "is_active")
