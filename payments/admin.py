"""Payment admin."""

from django.contrib import admin

from payments.models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("tracking_code", "store", "user", "gateway", "amount", "status", "ref_id", "created_at")
    list_filter = ("store", "gateway", "status")
    search_fields = ("tracking_code", "authority", "ref_id", "user__phone")
    readonly_fields = ("tracking_code", "authority", "ref_id", "verify_data", "paid_at")
