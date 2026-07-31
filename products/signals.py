"""Product cache invalidation signals."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.cache import cache_manager
from products.models import (
    Brand,
    Category,
    Inventory,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductVariant,
)


def _invalidate(store_id: int | None) -> None:
    if store_id:
        cache_manager.invalidate_products(store_id)


def _store_id_from_inventory(instance: Inventory) -> int | None:
    if instance.product_id:
        return instance.product.store_id
    if instance.variant_id:
        return instance.variant.product.store_id
    return None


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def invalidate_on_product(sender, instance, **kwargs):
    _invalidate(instance.store_id)


@receiver(post_save, sender=Category)
@receiver(post_delete, sender=Category)
def invalidate_on_category(sender, instance, **kwargs):
    _invalidate(instance.store_id)


@receiver(post_save, sender=Brand)
@receiver(post_delete, sender=Brand)
def invalidate_on_brand(sender, instance, **kwargs):
    _invalidate(instance.store_id)


@receiver(post_save, sender=ProductAttribute)
@receiver(post_delete, sender=ProductAttribute)
def invalidate_on_attribute(sender, instance, **kwargs):
    _invalidate(instance.store_id)


@receiver(post_save, sender=ProductAttributeValue)
@receiver(post_delete, sender=ProductAttributeValue)
def invalidate_on_attribute_value(sender, instance, **kwargs):
    _invalidate(instance.attribute.store_id)


@receiver(post_save, sender=ProductVariant)
@receiver(post_delete, sender=ProductVariant)
def invalidate_on_variant(sender, instance, **kwargs):
    _invalidate(instance.product.store_id)


@receiver(post_save, sender=Inventory)
@receiver(post_delete, sender=Inventory)
def invalidate_on_inventory(sender, instance, **kwargs):
    _invalidate(_store_id_from_inventory(instance))
