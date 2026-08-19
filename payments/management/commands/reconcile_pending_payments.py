"""Reconcile pending (redirected) Zarinpal payments via inquiry."""

from django.core.management.base import BaseCommand

from payments.services.payment import PaymentService
from tenants.models import Store


class Command(BaseCommand):
    help = "استعلام تراکنش‌های معلق زرین‌پال و تکمیل پرداخت‌های موفق بدون callback"

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=30,
            help="حداقل سن تراکنش redirected بر حسب دقیقه (پیش‌فرض: ۳۰)",
        )
        parser.add_argument("--store", type=str, help="فیلتر بر اساس slug فروشگاه")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="فقط استعلام کن؛ verify و ساخت سفارش انجام نشود",
        )

    def handle(self, *args, **options):
        store = None
        store_slug = options.get("store")
        if store_slug:
            store = Store.objects.filter(slug=store_slug).first()
            if not store:
                self.stderr.write(self.style.ERROR(f"فروشگاه «{store_slug}» یافت نشد."))
                return

        stats = PaymentService().reconcile_pending_payments(
            minutes=options["minutes"],
            store=store,
            dry_run=options["dry_run"],
        )
        prefix = "dry-run " if options["dry_run"] else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}checked={stats['checked']} verified={stats['verified']} "
                f"skipped={stats['skipped']} failed={stats['failed']}"
            )
        )
