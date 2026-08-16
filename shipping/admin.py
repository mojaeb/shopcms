"""Shipping admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from shipping.models import ShippingMethod, ShippingPrice, ShippingRule, ShippingZone


class ShippingPriceInline(TabularInline):
    model = ShippingPrice
    extra = 0


class ShippingRuleInline(TabularInline):
    model = ShippingRule
    extra = 0


@admin.register(ShippingZone)
class ShippingZoneAdmin(ModelAdmin):
    list_display = ("name", "store", "is_active")
    list_filter = ("store", "is_active")


@admin.register(ShippingMethod)
class ShippingMethodAdmin(ModelAdmin):
    list_display = ("name", "store", "provider", "calculation_mode", "is_active", "sort_order")
    list_filter = ("store", "provider", "calculation_mode", "is_active")
    inlines = [ShippingPriceInline, ShippingRuleInline]


@admin.register(ShippingPrice)
class ShippingPriceAdmin(ModelAdmin):
    list_display = ("method", "from_city", "to_city", "weight_min_kg", "weight_max_kg", "price")
    list_filter = ("method__store", "method")


@admin.register(ShippingRule)
class ShippingRuleAdmin(ModelAdmin):
    list_display = ("name", "method", "zone", "priority", "is_active")
    list_filter = ("method__store", "is_active")
