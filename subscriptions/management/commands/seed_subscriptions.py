"""Seed subscription demo data."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from plugins.services.plugin import PluginService
from products.enums import ProductStatus, ProductType
from products.models import Product
from subscriptions.enums import BillingInterval
from subscriptions.services.subscription import SubscriptionService
from tenants.enums import StoreType
from tenants.models import Domain, Store, Theme


class Command(BaseCommand):
    help = "Seed subscription product and plan"

    def handle(self, *args, **options):
        theme, _ = Theme.objects.get_or_create(
            slug="default",
            defaults={"name": "Default", "directory": "default", "is_default": True},
        )
        store, _ = Store.objects.get_or_create(
            slug="sub-shop",
            defaults={
                "name": "Subscription Shop",
                "default_theme": theme,
                "status": "active",
                "store_type": StoreType.SUBSCRIPTION,
            },
        )
        Domain.objects.get_or_create(store=store, domain="sub.local", defaults={"is_primary": True})

        PluginService().sync_registry_to_db()
        PluginService().install_defaults(store)

        product, _ = Product.objects.get_or_create(
            store=store,
            slug="premium-plan",
            defaults={
                "name": "اشتراک پریمیوم",
                "description": "دسترسی ماهانه",
                "product_type": ProductType.SUBSCRIPTION,
                "status": ProductStatus.ACTIVE,
                "base_price": 99000,
            },
        )

        if hasattr(product, "subscription_plan") and product.subscription_plan:
            self.stdout.write("Subscription demo already exists.")
            return

        SubscriptionService().create_plan(
            store,
            product.id,
            BillingInterval.MONTHLY,
            Decimal("99000"),
            trial_days=7,
            grace_period_days=3,
        )
        self.stdout.write(self.style.SUCCESS(f"Subscription product seeded: {product.slug}"))
