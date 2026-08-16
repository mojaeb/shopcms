"""Wishlist admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from wishlists.models import WishlistItem


@admin.register(WishlistItem)
class WishlistItemAdmin(ModelAdmin):
    list_display = ("user", "product", "store", "created_at")
    list_filter = ("store",)
    search_fields = ("user__phone", "product__name")
