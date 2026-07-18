"""Tax admin."""

from django.contrib import admin

from taxes.models import TaxRule


@admin.register(TaxRule)
class TaxRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "scope", "rate_percent", "is_active", "priority")
    list_filter = ("store", "scope", "is_active")
