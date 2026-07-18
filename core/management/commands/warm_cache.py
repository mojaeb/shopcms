"""Warm platform caches."""

from django.core.management.base import BaseCommand

from core.services.maintenance import MaintenanceService


class Command(BaseCommand):
    help = "Warm store, CMS, and product filter caches"

    def add_arguments(self, parser):
        parser.add_argument("--store", type=str, help="Store slug filter")

    def handle(self, *args, **options):
        service = MaintenanceService()
        result = service.warm_active_stores(store_slug=options.get("store"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Warmed cache for {result['warmed_stores']} store(s)."
            )
        )
