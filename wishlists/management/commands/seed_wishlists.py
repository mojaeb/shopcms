"""Seed wishlist plugin."""

from django.core.management.base import BaseCommand

from tenants.models import Plugin, Store, StorePlugin


class Command(BaseCommand):
    help = "Enable wishlist plugin for development stores"

    def handle(self, *args, **options):
        plugin, _ = Plugin.objects.get_or_create(
            codename="wishlist",
            defaults={"name": "Wishlist", "description": "Customer wishlist", "is_active": True},
        )
        for store in Store.objects.all():
            StorePlugin.objects.update_or_create(
                store=store,
                plugin=plugin,
                defaults={"is_enabled": True},
            )
        self.stdout.write(self.style.SUCCESS("Wishlist plugin enabled for all stores."))
