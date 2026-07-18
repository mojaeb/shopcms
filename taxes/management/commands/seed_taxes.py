"""Seed tax plugin and sample rules."""

from django.core.management.base import BaseCommand

from taxes.models import TaxRule
from tenants.models import Plugin, Store, StorePlugin


class Command(BaseCommand):
    help = "Enable tax plugin and create sample tax rules for development stores"

    def handle(self, *args, **options):
        plugin, _ = Plugin.objects.get_or_create(
            codename="tax",
            defaults={
                "name": "Tax",
                "description": "Tax calculation",
                "is_active": True,
            },
        )

        for store in Store.objects.all():
            StorePlugin.objects.update_or_create(
                store=store,
                plugin=plugin,
                defaults={"is_enabled": store.tax_enabled},
            )

            if store.tax_enabled:
                TaxRule.objects.get_or_create(
                    store=store,
                    name="Default VAT",
                    defaults={
                        "rate_percent": store.tax_percent,
                        "scope": "all",
                        "is_active": True,
                        "priority": 0,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Tax plugin and rules seeded successfully."))
