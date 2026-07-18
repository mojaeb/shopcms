"""Seed sample shipping methods."""

from django.core.management.base import BaseCommand

from shipping.enums import CalculationMode, ShippingProviderType
from shipping.models import ShippingMethod, ShippingPrice, ShippingZone
from tenants.models import Store, StoreSetting


class Command(BaseCommand):
    help = "Seed sample shipping methods for development"

    def handle(self, *args, **options):
        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("Run seed_store first."))
            return

        StoreSetting.objects.update_or_create(
            store=store,
            group="shipping",
            key="origin",
            defaults={"value": {"origin_city": "مشهد", "origin_province": "خراسان رضوی", "free_shipping_threshold": 5000000}},
        )

        zone, _ = ShippingZone.objects.get_or_create(
            store=store,
            name="سراسر کشور",
            defaults={"provinces": [], "cities": [], "is_active": True},
        )

        post, _ = ShippingMethod.objects.get_or_create(
            store=store,
            slug="post-fixed",
            defaults={
                "name": "پست - هزینه ثابت",
                "provider": ShippingProviderType.POST,
                "calculation_mode": CalculationMode.FIXED,
                "config": {"fixed_price": 80000, "origin_city": "مشهد"},
                "zone": zone,
                "is_active": True,
                "sort_order": 1,
                "estimated_days": 5,
            },
        )

        tipax, _ = ShippingMethod.objects.get_or_create(
            store=store,
            slug="tipax-distance",
            defaults={
                "name": "تیپاکس - بر اساس مسافت",
                "provider": ShippingProviderType.TIPAX,
                "calculation_mode": CalculationMode.DISTANCE,
                "config": {"origin_city": "مشهد", "fixed_price": 120000},
                "zone": zone,
                "is_active": True,
                "sort_order": 2,
                "estimated_days": 3,
            },
        )

        ShippingPrice.objects.get_or_create(
            method=tipax,
            from_city="مشهد",
            to_city="تهران",
            defaults={"price": 180000},
        )
        ShippingPrice.objects.get_or_create(
            method=tipax,
            from_city="مشهد",
            to_city="اصفهان",
            defaults={"price": 150000},
        )

        weight_method, _ = ShippingMethod.objects.get_or_create(
            store=store,
            slug="post-weight",
            defaults={
                "name": "پست - بر اساس وزن",
                "provider": ShippingProviderType.POST,
                "calculation_mode": CalculationMode.WEIGHT,
                "config": {"origin_city": "مشهد", "fixed_price": 100000},
                "zone": zone,
                "is_active": True,
                "sort_order": 3,
                "estimated_days": 4,
            },
        )
        ShippingPrice.objects.get_or_create(
            method=weight_method,
            from_city="",
            to_city="",
            weight_min_kg=0,
            weight_max_kg=2,
            defaults={"price": 90000},
        )
        ShippingPrice.objects.get_or_create(
            method=weight_method,
            from_city="",
            to_city="",
            weight_min_kg=2,
            weight_max_kg=5,
            defaults={"price": 150000},
        )

        ShippingMethod.objects.get_or_create(
            store=store,
            slug="free-shipping",
            defaults={
                "name": "ارسال رایگان",
                "provider": ShippingProviderType.FREE,
                "calculation_mode": CalculationMode.FIXED,
                "config": {"fallback_price": 0},
                "free_shipping_threshold": 5000000,
                "zone": zone,
                "is_active": True,
                "sort_order": 0,
                "estimated_days": 5,
            },
        )

        self.stdout.write(self.style.SUCCESS("Shipping methods seeded successfully."))
