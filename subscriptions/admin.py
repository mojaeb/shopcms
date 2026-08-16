"""Subscriptions admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from subscriptions.models import CustomerSubscription, SubscriptionPlan, SubscriptionRenewal


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ("product", "store", "interval", "price", "trial_days", "is_active")
    list_filter = ("store", "interval")


@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(ModelAdmin):
    list_display = ("user", "product", "status", "current_period_end", "auto_renew")
    list_filter = ("store", "status")


@admin.register(SubscriptionRenewal)
class SubscriptionRenewalAdmin(ModelAdmin):
    list_display = ("subscription", "period_start", "period_end", "amount", "status")
