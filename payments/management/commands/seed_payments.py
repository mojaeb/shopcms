"""Seed payment gateway settings."""

from django.core.management.base import BaseCommand

from tenants.models import Store, StoreSetting


class Command(BaseCommand):
    help = "Seed payment gateway settings for development"

    def handle(self, *args, **options):
        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("Run seed_store first."))
            return

        settings = {
            "gateways": ["zarinpal", "idpay", "mellat", "pasargad"],
            "default_gateway": "zarinpal",
            "zarinpal": {"merchant_id": "sandbox-merchant", "sandbox": True},
            "idpay": {"api_key": "sandbox-key", "sandbox": True},
            "mellat": {"terminal_id": "sandbox-terminal", "sandbox": True},
            "pasargad": {"merchant_code": "sandbox-pasargad", "sandbox": True},
        }

        for key, value in settings.items():
            StoreSetting.objects.update_or_create(
                store=store,
                group="payment",
                key=key,
                defaults={"value": value},
            )

        self.stdout.write(self.style.SUCCESS("Payment settings seeded successfully."))
