"""Order admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from orders.models import Invoice, Order, OrderHistory, OrderItem, Shipment


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("line_total",)


class OrderHistoryInline(TabularInline):
    model = OrderHistory
    extra = 0
    readonly_fields = ("status", "note", "created_by", "created_at")


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ("order_number", "store", "user", "status", "total", "created_at")
    list_filter = ("store", "status")
    search_fields = ("order_number", "user__phone")
    inlines = [OrderItemInline, OrderHistoryInline]


@admin.register(Shipment)
class ShipmentAdmin(ModelAdmin):
    list_display = ("order", "status", "tracking_code", "carrier", "shipped_at")
    list_filter = ("status",)


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ("invoice_number", "order", "issued_at", "pdf_url")
