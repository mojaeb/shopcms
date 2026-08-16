"""Seed fixed-price Post and Tipax shipping methods."""

from django.core.management.base import BaseCommand

from shipping.enums import CalculationMode, ShippingProviderType
from shipping.models import ShippingMethod, ShippingZone
from tenants.models import Store, StoreSetting


class Command(BaseCommand):
    help = "Seed fixed-price Post and Tipax shipping methods for development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--store",
            default="shop1",
            help="Store slug to seed (default: shop1)",
        )

    def handle(self, *args, **options):
        store_slug = options["store"]
        store = Store.objects.filter(slug=store_slug).first()
        if not store:
            self.stdout.write(self.style.WARNING(f"Store '{store_slug}' not found. Run seed_store first."))
            return

        StoreSetting.objects.update_or_create(
            store=store,
            group="shipping",
            key="origin",
            defaults={
                "value": {
                    "origin_city": "مشهد",
                    "origin_province": "خراسان رضوی",
                    "free_shipping_threshold": 0,
                },
            },
        )
        StoreSetting.objects.update_or_create(
            store=store,
            group="shipping",
            key="providers",
            defaults={"value": ["post", "tipax"]},
        )
        StoreSetting.objects.update_or_create(
            store=store,
            group="shipping",
            key="default_provider",
            defaults={"value": "post"},
        )
        StoreSetting.objects.update_or_create(
            store=store,
            group="shipping",
            key="post",
            defaults={"value": {"mode": "fixed", "fixed_price": 80000}},
        )
        StoreSetting.objects.update_or_create(
            store=store,
            group="shipping",
            key="tipax",
            defaults={"value": {"mode": "fixed", "fixed_price": 120000}},
        )
        StoreSetting.objects.update_or_create(
            store=store,
            group="shipping",
            key="free_shipping_threshold",
            defaults={"value": 0},
        )

        zone, _ = ShippingZone.objects.update_or_create(
            store=store,
            name="سراسر کشور",
            defaults={"provinces": [], "cities": [], "is_active": True},
        )

        ShippingMethod.objects.update_or_create(
            store=store,
            slug="post-fixed",
            defaults={
                "name": "پست",
                "provider": ShippingProviderType.POST,
                "calculation_mode": CalculationMode.FIXED,
                "config": {"fixed_price": 80000, "origin_city": "مشهد"},
                "zone": zone,
                "is_active": True,
                "sort_order": 1,
                "estimated_days": 5,
                "min_order_amount": 0,
            },
        )

        ShippingMethod.objects.update_or_create(
            store=store,
            slug="tipax-fixed",
            defaults={
                "name": "تیپاکس",
                "provider": ShippingProviderType.TIPAX,
                "calculation_mode": CalculationMode.FIXED,
                "config": {"fixed_price": 120000, "origin_city": "مشهد"},
                "zone": zone,
                "is_active": True,
                "sort_order": 2,
                "estimated_days": 3,
                "min_order_amount": 0,
            },
        )

        # Keep checkout clean: disable older sample methods if present.
        ShippingMethod.objects.filter(
            store=store,
            slug__in=["tipax-distance", "post-weight", "free-shipping"],
        ).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            "Shipping seeded: post-fixed (80000) and tipax-fixed (120000)."
        ))
