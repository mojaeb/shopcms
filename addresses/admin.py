"""Address admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from addresses.models import CustomerAddress


@admin.register(CustomerAddress)
class CustomerAddressAdmin(ModelAdmin):
    list_display = ("full_name", "user", "store", "city", "province", "is_default", "updated_at")
    list_filter = ("store", "province", "is_default")
    search_fields = ("full_name", "phone", "user__phone", "city", "postal_code")
