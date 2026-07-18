"""Seed sample coupons."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from carts.enums import DiscountType
from carts.models import Coupon, GiftCard
from tenants.models import Plugin, Store, StorePlugin


class Command(BaseCommand):
    help = "Seed sample coupons and gift cards for development"

    def handle(self, *args, **options):
        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("Run seed_store first."))
            return

        plugin, _ = Plugin.objects.get_or_create(
            codename="coupon",
            defaults={"name": "Coupons", "description": "Discount coupons", "is_active": True},
        )
        StorePlugin.objects.update_or_create(store=store, plugin=plugin, defaults={"is_enabled": True})

        coupons = [
            {
                "code": "WELCOME10",
                "discount_type": DiscountType.PERCENTAGE,
                "value": 10,
                "min_order_amount": 100000,
                "first_purchase_only": True,
            },
            {
                "code": "SAVE50K",
                "discount_type": DiscountType.FIXED,
                "value": 50000,
                "min_order_amount": 500000,
            },
        ]

        for data in coupons:
            coupon, created = Coupon.objects.get_or_create(
                store=store,
                code=data["code"],
                defaults={
                    **data,
                    "is_active": True,
                    "valid_from": timezone.now(),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created coupon: {coupon.code}"))

        gift, created = GiftCard.objects.get_or_create(
            store=store,
            code="GIFT100K",
            defaults={
                "initial_balance": 100000,
                "balance": 100000,
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created gift card: {gift.code}"))

        self.stdout.write(self.style.SUCCESS("Coupons seeded successfully."))
