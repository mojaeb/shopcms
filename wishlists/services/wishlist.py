"""Wishlist service layer."""

import logging

from django.db import transaction

from products.enums import ProductStatus
from products.models import Product
from products.services.product import ProductService
from tenants.models import StorePlugin
from wishlists.models import WishlistItem

logger = logging.getLogger(__name__)


class WishlistError(Exception):
    pass


class WishlistService:
    """Customer wishlist operations."""

    def __init__(self):
        self.product_service = ProductService()

    def is_active(self, store) -> bool:
        from plugins.services.plugin import PluginService

        return PluginService().is_enabled(store, "wishlist")

    def list_items(self, user, store):
        return (
            WishlistItem.objects.filter(store=store, user=user)
            .select_related("product", "product__category", "product__brand")
            .prefetch_related("product__images", "product__inventory_items")
        )

    def get_count(self, user, store) -> int:
        return WishlistItem.objects.filter(store=store, user=user).count()

    def is_in_wishlist(self, user, store, product_slug: str) -> bool:
        return WishlistItem.objects.filter(
            store=store,
            user=user,
            product__slug=product_slug,
        ).exists()

    @transaction.atomic
    def add_item(self, user, store, product_slug: str) -> WishlistItem:
        if not self.is_active(store):
            raise WishlistError("علاقه‌مندی‌ها برای این فروشگاه فعال نیست")

        product = self._get_product(store, product_slug)
        item, created = WishlistItem.objects.get_or_create(store=store, user=user, product=product)
        if created:
            logger.info("Wishlist add: user=%s product=%s", user.pk, product.slug)
        return item

    @transaction.atomic
    def remove_item(self, user, store, product_id: int | None = None, product_slug: str | None = None) -> None:
        qs = WishlistItem.objects.filter(store=store, user=user)
        if product_id:
            qs = qs.filter(product_id=product_id)
        elif product_slug:
            qs = qs.filter(product__slug=product_slug)
        else:
            raise WishlistError("محصول مشخص نیست")

        deleted, _ = qs.delete()
        if not deleted:
            raise WishlistError("آیتم در علاقه‌مندی‌ها یافت نشد")

    @transaction.atomic
    def toggle_item(self, user, store, product_slug: str) -> dict:
        if self.is_in_wishlist(user, store, product_slug):
            self.remove_item(user, store, product_slug=product_slug)
            return {"in_wishlist": False}
        self.add_item(user, store, product_slug)
        return {"in_wishlist": True}

    def serialize_item(self, item: WishlistItem) -> dict:
        return self.product_service.serialize_product_list(item.product)

    def _get_product(self, store, product_slug: str) -> Product:
        product = Product.objects.filter(
            store=store,
            slug=product_slug,
            status=ProductStatus.ACTIVE,
        ).first()
        if not product:
            raise WishlistError("محصول یافت نشد")
        return product
