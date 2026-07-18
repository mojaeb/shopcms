"""Built-in platform plugins."""

from django.urls import path
from django.views.generic import TemplateView
from ninja import Router

from plugins.base import BasePlugin, PluginSettingField
from plugins.registry import register
from tenants.enums import StoreType


def _stub_router(codename: str, label: str) -> Router:
    router = Router()

    @router.get("/info")
    def plugin_info(request):
        return {"codename": codename, "name": label, "status": "ready"}

    return router


class StoreTypePlugin(BasePlugin):
    provides = ["models", "api", "admin", "settings"]

    def get_api_router(self):
        return _stub_router(self.codename, self.name)


@register
class PhysicalPlugin(StoreTypePlugin):
    codename = "physical"
    name = "Physical Goods"
    description = "Physical products with shipping and inventory"
    compatible_store_types = [StoreType.PHYSICAL]
    settings_schema = [
        PluginSettingField("track_inventory", "Track inventory", "boolean", True),
        PluginSettingField("allow_backorder", "Allow backorder", "boolean", False),
    ]


@register
class DigitalDownloadPlugin(StoreTypePlugin):
    codename = "digital_download"
    name = "Digital Download"
    description = "Digital file downloads with license limits"
    compatible_store_types = [StoreType.DIGITAL_DOWNLOAD]
    settings_schema = [
        PluginSettingField("max_downloads", "Max downloads per purchase", "integer", 5),
        PluginSettingField("link_expire_hours", "Download link expiry (hours)", "integer", 72),
    ]


@register
class SubscriptionPlugin(StoreTypePlugin):
    codename = "subscription"
    name = "Subscription"
    description = "Recurring subscription products"
    compatible_store_types = [StoreType.SUBSCRIPTION]
    settings_schema = [
        PluginSettingField("grace_period_days", "Grace period days", "integer", 3),
        PluginSettingField("auto_renew", "Auto renew", "boolean", True),
    ]


@register
class BookingPlugin(StoreTypePlugin):
    codename = "booking"
    name = "Booking"
    description = "Service booking and reservations"
    compatible_store_types = [StoreType.BOOKING]
    provides = ["models", "api", "admin", "templates", "settings"]

    settings_schema = [
        PluginSettingField("slot_duration_minutes", "Slot duration (minutes)", "integer", 60),
        PluginSettingField("max_advance_days", "Max advance booking days", "integer", 30),
    ]

    def get_urlpatterns(self):
        return [
            path("", TemplateView.as_view(template_name="plugins/booking.html"), name="plugin_booking"),
        ]

    def get_template_pages(self):
        return {"booking": "plugins/booking.html"}


@register
class AppointmentPlugin(StoreTypePlugin):
    codename = "appointment"
    name = "Appointment"
    description = "Appointment scheduling"
    compatible_store_types = [StoreType.APPOINTMENT]
    provides = ["models", "api", "admin", "templates", "settings"]

    settings_schema = [
        PluginSettingField("reminder_hours", "Reminder before (hours)", "integer", 24),
    ]

    def get_urlpatterns(self):
        return [
            path("", TemplateView.as_view(template_name="plugins/appointment.html"), name="plugin_appointment"),
        ]

    def get_template_pages(self):
        return {"appointment": "plugins/appointment.html"}


@register
class RentalPlugin(StoreTypePlugin):
    codename = "rental"
    name = "Rental"
    description = "Rental products with date ranges"
    compatible_store_types = [StoreType.RENTAL]
    settings_schema = [
        PluginSettingField("min_rental_days", "Minimum rental days", "integer", 1),
        PluginSettingField("deposit_percent", "Deposit percent", "integer", 20),
    ]


@register
class PrintOnDemandPlugin(StoreTypePlugin):
    codename = "print_on_demand"
    name = "Print on Demand"
    description = "Custom print products"
    compatible_store_types = [StoreType.PRINT_ON_DEMAND]
    settings_schema = [
        PluginSettingField("allow_custom_text", "Allow custom text", "boolean", True),
        PluginSettingField("production_days", "Production days", "integer", 3),
    ]


class FeaturePlugin(BasePlugin):
    provides = ["api", "settings"]

    def get_api_router(self):
        return _stub_router(self.codename, self.name)


@register
class BlogFeaturePlugin(FeaturePlugin):
    codename = "blog"
    name = "Blog"
    description = "Blog and articles"
    compatible_store_types = []


@register
class CommentsFeaturePlugin(FeaturePlugin):
    codename = "comments"
    name = "Comments"
    description = "Product reviews and comments"
    compatible_store_types = []


@register
class WishlistFeaturePlugin(FeaturePlugin):
    codename = "wishlist"
    name = "Wishlist"
    description = "Customer wishlist"
    compatible_store_types = []


@register
class CouponFeaturePlugin(FeaturePlugin):
    codename = "coupon"
    name = "Coupons"
    description = "Discount coupons and gift cards"
    compatible_store_types = []


@register
class TaxFeaturePlugin(FeaturePlugin):
    codename = "tax"
    name = "Tax"
    description = "Tax calculation"
    compatible_store_types = []


@register
class ShippingFeaturePlugin(FeaturePlugin):
    codename = "shipping"
    name = "Shipping"
    description = "Shipping methods"
    compatible_store_types = [StoreType.PHYSICAL]


@register
class PaymentFeaturePlugin(FeaturePlugin):
    codename = "payment"
    name = "Payment"
    description = "Payment gateways"
    compatible_store_types = []


@register
class InventoryFeaturePlugin(FeaturePlugin):
    codename = "inventory"
    name = "Inventory"
    description = "Stock management"
    compatible_store_types = [StoreType.PHYSICAL]
