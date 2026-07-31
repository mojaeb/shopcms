"""CMS cache invalidation signals."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from cms.models import (
    Banner,
    ContentBlock,
    LayoutSettings,
    Menu,
    MenuItem,
    Page,
    Shortcode,
    Slide,
    Slider,
    Widget,
)
from cms.services.cache import CMSCacheService
from cms.services.shortcodes import invalidate_shortcode_cache
from core.cache import cache_manager


def _invalidate_store(store):
    if store:
        CMSCacheService().invalidate_store(store)


@receiver([post_save, post_delete], sender=Page)
@receiver([post_save, post_delete], sender=Menu)
@receiver([post_save, post_delete], sender=Banner)
@receiver([post_save, post_delete], sender=Slider)
@receiver([post_save, post_delete], sender=Widget)
@receiver([post_save, post_delete], sender=LayoutSettings)
def invalidate_on_store_model(sender, instance, **kwargs):
    _invalidate_store(instance.store)


@receiver([post_save, post_delete], sender=MenuItem)
def invalidate_on_menu_item(sender, instance, **kwargs):
    _invalidate_store(instance.menu.store)


@receiver([post_save, post_delete], sender=Slide)
def invalidate_on_slide(sender, instance, **kwargs):
    _invalidate_store(instance.slider.store)


@receiver([post_save, post_delete], sender=ContentBlock)
def invalidate_on_block(sender, instance, **kwargs):
    _invalidate_store(instance.page.store)


@receiver([post_save, post_delete], sender=Shortcode)
def invalidate_on_shortcode(sender, instance, **kwargs):
    store = instance.store
    invalidate_shortcode_cache(store)
    CMSCacheService().invalidate_store(store)
    # Shortcodes can appear in product descriptions and blog posts.
    cache_manager.invalidate_blog(store.id)
    cache_manager.invalidate_products(store.id)
