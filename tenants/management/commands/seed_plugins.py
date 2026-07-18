"""Seed default plugins."""

from django.core.management.base import BaseCommand

from plugins.services.plugin import PluginService


class Command(BaseCommand):
    help = "Seed default platform plugins from registry"

    def handle(self, *args, **options):
        created = PluginService().sync_registry_to_db()
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created {created} plugins from registry."))
        self.stdout.write(self.style.SUCCESS("Plugins seeded successfully."))
