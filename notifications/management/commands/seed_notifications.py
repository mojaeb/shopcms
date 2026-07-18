"""Seed default notification channels."""

from django.core.management.base import BaseCommand

from notifications.enums import ChannelType
from notifications.models import NotificationChannel
from tenants.models import Domain, Store, Theme


class Command(BaseCommand):
    help = "Seed default notification channels for demo store"

    def handle(self, *args, **options):
        theme, _ = Theme.objects.get_or_create(
            slug="default",
            defaults={"name": "Default", "directory": "default", "is_default": True},
        )
        store, _ = Store.objects.get_or_create(
            slug="shop1",
            defaults={"name": "Demo Shop", "default_theme": theme, "status": "active"},
        )
        Domain.objects.get_or_create(store=store, domain="shop1.local", defaults={"is_primary": True})

        defaults = [
            (ChannelType.SMS, "console_sms"),
            (ChannelType.EMAIL, "console_email"),
            (ChannelType.PUSH, "console_push"),
        ]
        for channel_type, provider in defaults:
            NotificationChannel.objects.get_or_create(
                store=store,
                channel_type=channel_type,
                provider=provider,
                defaults={"is_default": True, "is_active": True, "config": {}},
            )

        self.stdout.write(self.style.SUCCESS("Notification channels seeded successfully."))
