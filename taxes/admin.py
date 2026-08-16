"""Tax admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from taxes.models import TaxRule


@admin.register(TaxRule)
class TaxRuleAdmin(ModelAdmin):
    list_display = ("name", "store", "scope", "rate_percent", "is_active", "priority")
    list_filter = ("store", "scope", "is_active")
