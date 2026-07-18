"""Seed default theme, store and domain."""

from django.core.management.base import BaseCommand

from tenants.models import Domain, Store, Theme


class Command(BaseCommand):
    help = "ایجاد تم، فروشگاه و دامنه نمونه برای توسعه"

    def handle(self, *args, **options):
        default_theme, created = Theme.objects.get_or_create(
            slug="default",
            defaults={
                "name": "تم پیش‌فرض",
                "directory": "default",
                "is_default": True,
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created default theme: {default_theme.slug}"))

        modern_theme, created = Theme.objects.get_or_create(
            slug="modern",
            defaults={
                "name": "تم مدرن",
                "directory": "modern",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created modern theme: {modern_theme.slug}"))

        minimal_theme, created = Theme.objects.get_or_create(
            slug="minimal",
            defaults={
                "name": "Minimal",
                "directory": "minimal",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created minimal theme: {minimal_theme.slug}"))

        round_theme, created = Theme.objects.get_or_create(
            slug="round",
            defaults={
                "name": "Round",
                "directory": "round",
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created round theme: {round_theme.slug}"))

        store, created = Store.objects.get_or_create(
            slug="shop1",
            defaults={
                "name": "فروشگاه نمونه",
                "store_type": "physical",
                "theme": round_theme,
                "default_theme": default_theme,
                "currency": "IRR",
                "status": "active",
                "tax_enabled": True,
                "tax_percent": 9,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created store: {store.slug}"))

        for domain_name in ("localhost", "127.0.0.1", "shop1.local"):
            domain, created = Domain.objects.get_or_create(
                domain=domain_name,
                defaults={
                    "store": store,
                    "is_primary": domain_name == "localhost",
                    "is_active": True,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created domain: {domain.domain}"))

        from tenants.services.theme_settings import ThemeSettingsService

        theme_config = ThemeSettingsService().ensure_sample_config(store)
        slide_count = len((theme_config.get("hero") or {}).get("slides") or [])
        self.stdout.write(
            self.style.SUCCESS(f"Theme settings ready for {store.slug} ({slide_count} hero slides)")
        )

        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))
