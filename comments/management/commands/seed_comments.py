"""Seed comments plugin."""

from django.core.management.base import BaseCommand

from tenants.models import Plugin, Store, StorePlugin


class Command(BaseCommand):
    help = "Enable comments plugin for development stores"

    def handle(self, *args, **options):
        plugin, _ = Plugin.objects.get_or_create(
            codename="comments",
            defaults={"name": "Comments", "description": "Product comments and reviews", "is_active": True},
        )
        for store in Store.objects.all():
            StorePlugin.objects.update_or_create(
                store=store,
                plugin=plugin,
                defaults={"is_enabled": True},
            )
        self.stdout.write(self.style.SUCCESS("Comments plugin enabled for all stores."))
