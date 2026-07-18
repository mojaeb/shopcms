"""Expire past-due subscriptions."""

from django.core.management.base import BaseCommand

from subscriptions.services.subscription import SubscriptionService
from tenants.models import Store


class Command(BaseCommand):
    help = "Mark expired subscriptions and past-due statuses"

    def add_arguments(self, parser):
        parser.add_argument("--store", type=str, help="Store slug filter")

    def handle(self, *args, **options):
        service = SubscriptionService()
        store_slug = options.get("store")
        if store_slug:
            store = Store.objects.get(slug=store_slug)
            count = service.expire_due_subscriptions(store=store)
        else:
            count = service.expire_due_subscriptions()
        self.stdout.write(self.style.SUCCESS(f"Processed subscriptions. Expired: {count}"))
