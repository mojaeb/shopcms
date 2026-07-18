"""Clear platform caches."""

from django.core.management.base import BaseCommand

from core.services.maintenance import MaintenanceService
from tenants.models import Store


class Command(BaseCommand):
    help = "Clear ShopCMS cache namespaces"

    def add_arguments(self, parser):
        parser.add_argument("--store", type=str, help="Store slug filter")
        parser.add_argument("--all", action="store_true", help="Clear all ShopCMS cache keys")

    def handle(self, *args, **options):
        service = MaintenanceService()
        if options.get("all"):
            deleted = service.clear_all_cache()
            self.stdout.write(self.style.SUCCESS(f"Cleared cache keys (pattern delete count: {deleted})"))
            return

        store_slug = options.get("store")
        if store_slug:
            store = Store.objects.get(slug=store_slug)
            deleted = service.clear_store_cache(store.id)
            self.stdout.write(
                self.style.SUCCESS(f"Cleared cache for store {store.slug} (pattern delete count: {deleted})")
            )
            return

        self.stdout.write(self.style.ERROR("Specify --store <slug> or --all"))
