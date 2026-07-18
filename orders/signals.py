"""Order cache invalidation signals."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.cache import cache_manager
from orders.models import Order


@receiver(post_save, sender=Order)
def invalidate_reports_on_order(sender, instance, **kwargs):
    cache_manager.invalidate_reports(instance.store_id)
