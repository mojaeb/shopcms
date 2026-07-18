"""Sync plugin registry to database."""

from django.core.management.base import BaseCommand

from plugins.services.plugin import PluginService


class Command(BaseCommand):
    help = "Sync registered plugins to Plugin table and install defaults for stores"

    def add_arguments(self, parser):
        parser.add_argument("--install-defaults", action="store_true", help="Install default plugins for all stores")

    def handle(self, *args, **options):
        service = PluginService()
        created = service.sync_registry_to_db()
        self.stdout.write(self.style.SUCCESS(f"Synced plugins. New records: {created}"))

        if options["install_defaults"]:
            from tenants.models import Store

            for store in Store.objects.all():
                service.install_defaults(store)
            self.stdout.write(self.style.SUCCESS("Default plugins installed for all stores."))
