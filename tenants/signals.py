"""Cache invalidation signals."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from tenants.models import Domain, Store, StoreSetting
from tenants.services.cache import StoreCacheService


@receiver(post_save, sender=Store)
@receiver(post_delete, sender=Store)
def invalidate_store_cache(sender, instance, **kwargs):
    StoreCacheService().invalidate_store(instance)


@receiver(post_save, sender=Domain)
@receiver(post_delete, sender=Domain)
def invalidate_domain_cache(sender, instance, **kwargs):
    cache_service = StoreCacheService()
    cache_service.invalidate_domain(instance.domain)
    cache_service.invalidate_store(instance.store)


@receiver(post_save, sender=StoreSetting)
@receiver(post_delete, sender=StoreSetting)
def invalidate_settings_cache(sender, instance, **kwargs):
    StoreCacheService().invalidate_store(instance.store)
