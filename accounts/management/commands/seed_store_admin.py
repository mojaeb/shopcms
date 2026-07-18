"""Seed a sample store admin user for local development."""

from django.core.management.base import BaseCommand

from accounts.services.auth import AuthService
from tenants.models import Store

DEFAULT_PHONE = "09120000000"
DEFAULT_STORE_SLUG = "shop1"


class Command(BaseCommand):
    help = "Create sample store admin for /manage/ panel"

    def add_arguments(self, parser):
        parser.add_argument("--phone", default=DEFAULT_PHONE, help="Admin phone")
        parser.add_argument("--store", default=DEFAULT_STORE_SLUG, help="Store slug")
        parser.add_argument("--first-name", default="Admin", help="First name")
        parser.add_argument("--last-name", default="Store", help="Last name")

    def handle(self, *args, **options):
        store = Store.objects.filter(slug=options["store"]).first()
        if not store:
            self.stderr.write(
                self.style.ERROR(
                    f"Store slug={options['store']} not found. Run seed_store first."
                )
            )
            return

        user, membership = AuthService().create_store_admin(
            phone=options["phone"],
            store=store,
            first_name=options["first_name"],
            last_name=options["last_name"],
            is_primary=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Store admin ready: {user.phone} on {store.slug} "
                f"(role={membership.role.codename})"
            )
        )
        self.stdout.write("Login: http://localhost:8000/login/?next=/manage/")
        self.stdout.write("Dev OTP: 12345")
