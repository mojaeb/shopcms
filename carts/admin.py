"""Cart admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from carts.models import Cart, CartItem, Coupon, CouponUsage, GiftCard, GiftCardUsage


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("unit_price",)


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("id", "store", "user", "session_key", "item_count", "updated_at")
    list_filter = ("store",)
    search_fields = ("user__phone", "session_key")
    inlines = [CartItemInline]

    @admin.display(description="تعداد آیتم")
    def item_count(self, obj):
        return obj.items.count()


class CouponM2MFilter(ModelAdmin):
    filter_horizontal = ("categories", "products", "allowed_users")


@admin.register(Coupon)
class CouponAdmin(CouponM2MFilter):
    list_display = ("code", "store", "discount_type", "scope", "value", "is_active", "used_count", "valid_until")
    list_filter = ("store", "discount_type", "scope", "is_active")
    search_fields = ("code",)


@admin.register(GiftCard)
class GiftCardAdmin(ModelAdmin):
    list_display = ("code", "store", "balance", "owner", "is_active", "valid_until")
    list_filter = ("store", "is_active")
    search_fields = ("code",)


@admin.register(CouponUsage)
class CouponUsageAdmin(ModelAdmin):
    list_display = ("coupon", "user", "order", "discount_amount", "created_at")
    list_filter = ("coupon__store",)


@admin.register(GiftCardUsage)
class GiftCardUsageAdmin(ModelAdmin):
    list_display = ("gift_card", "user", "order", "amount", "created_at")
    list_filter = ("gift_card__store",)
