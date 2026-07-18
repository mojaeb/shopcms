"""Subscription lifecycle service."""

import logging
from datetime import timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

from orders.models import Order
from plugins.services.plugin import PluginService
from products.models import Product
from subscriptions.enums import BillingInterval, RenewalStatus, SubscriptionStatus
from subscriptions.models import CustomerSubscription, SubscriptionPlan, SubscriptionRenewal

logger = logging.getLogger(__name__)

DEFAULT_GRACE_DAYS = 3


class SubscriptionError(Exception):
    pass


class SubscriptionService:
    """Create, renew, cancel, and expire subscriptions."""

    PLUGIN_CODENAME = "subscription"

    def is_active(self, store) -> bool:
        return PluginService().is_enabled(store, self.PLUGIN_CODENAME)

    def get_plugin_settings(self, store) -> dict:
        settings = PluginService().get_settings(store, self.PLUGIN_CODENAME)
        return {
            "grace_period_days": int(settings.get("grace_period_days", DEFAULT_GRACE_DAYS)),
            "auto_renew": bool(settings.get("auto_renew", True)),
        }

    def create_plan(
        self,
        store,
        product_id: int,
        interval: str,
        price: Decimal,
        interval_count: int = 1,
        trial_days: int = 0,
        grace_period_days: int = 3,
    ) -> SubscriptionPlan:
        product = Product.objects.get(pk=product_id, store=store)
        plan, _ = SubscriptionPlan.objects.update_or_create(
            product=product,
            defaults={
                "store": store,
                "interval": interval,
                "interval_count": interval_count,
                "trial_days": trial_days,
                "grace_period_days": grace_period_days,
                "price": price,
                "is_active": True,
            },
        )
        if product.product_type != "subscription":
            product.product_type = "subscription"
            product.save(update_fields=["product_type", "updated_at"])
        return plan

    def get_plan(self, store, product_id: int) -> SubscriptionPlan | None:
        return SubscriptionPlan.objects.filter(store=store, product_id=product_id, is_active=True).first()

    @transaction.atomic
    def create_from_order(self, order: Order) -> list[CustomerSubscription]:
        if not self.is_active(order.store) or not order.user_id:
            return []

        created = []
        for item in order.items.all():
            plan = self.get_plan(order.store, item.product_id)
            if not plan:
                continue

            existing = CustomerSubscription.objects.filter(
                store=order.store,
                user=order.user,
                product_id=item.product_id,
                status__in=[SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE],
            ).first()
            if existing:
                self.renew(existing, payment_ref=order.order_number, amount=plan.price)
                created.append(existing)
                continue

            now = timezone.now()
            trial_ends = now + timedelta(days=plan.trial_days) if plan.trial_days else None
            period_start = now
            period_end = self._add_interval(period_start, plan.interval, plan.interval_count)
            if trial_ends:
                period_end = trial_ends

            status = SubscriptionStatus.TRIALING if trial_ends else SubscriptionStatus.ACTIVE
            sub = CustomerSubscription.objects.create(
                store=order.store,
                user=order.user,
                product_id=item.product_id,
                plan=plan,
                initial_order=order,
                status=status,
                interval=plan.interval,
                interval_count=plan.interval_count,
                price=plan.price,
                auto_renew=self.get_plugin_settings(order.store)["auto_renew"],
                started_at=now,
                current_period_start=period_start,
                current_period_end=period_end,
                trial_ends_at=trial_ends,
            )
            SubscriptionRenewal.objects.create(
                subscription=sub,
                period_start=period_start,
                period_end=period_end,
                amount=item.line_total,
                status=RenewalStatus.SUCCESS,
                payment_ref=order.order_number,
                note="initial purchase",
            )
            created.append(sub)

        if created:
            logger.info("Created %s subscriptions for order %s", len(created), order.order_number)
        return created

    @transaction.atomic
    def renew(
        self,
        subscription: CustomerSubscription,
        payment_ref: str = "",
        amount: Decimal | None = None,
    ) -> CustomerSubscription:
        self.refresh_status(subscription)
        if subscription.status in (SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED):
            raise SubscriptionError("اشتراک قابل تمدید نیست")

        now = timezone.now()
        period_start = max(subscription.current_period_end, now)
        period_end = self._add_interval(period_start, subscription.interval, subscription.interval_count)

        subscription.current_period_start = period_start
        subscription.current_period_end = period_end
        subscription.trial_ends_at = None
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.expires_at = None
        subscription.renewal_count += 1
        subscription.save()

        SubscriptionRenewal.objects.create(
            subscription=subscription,
            period_start=period_start,
            period_end=period_end,
            amount=amount if amount is not None else subscription.price,
            status=RenewalStatus.SUCCESS,
            payment_ref=payment_ref,
            note="renewal",
        )
        return subscription

    @transaction.atomic
    def cancel(self, subscription: CustomerSubscription, immediate: bool = False) -> CustomerSubscription:
        now = timezone.now()
        subscription.canceled_at = now
        subscription.auto_renew = False
        if immediate:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.expires_at = now
        else:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.expires_at = subscription.current_period_end
        subscription.save()
        return subscription

    @transaction.atomic
    def expire_due_subscriptions(self, store=None) -> int:
        now = timezone.now()
        qs = CustomerSubscription.objects.filter(
            status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE, SubscriptionStatus.CANCELED],
        )
        if store:
            qs = qs.filter(store=store)

        expired_count = 0
        for sub in qs.select_related("plan", "store"):
            self.refresh_status(sub)
            grace_days = sub.plan.grace_period_days if sub.plan else DEFAULT_GRACE_DAYS
            plugin_settings = self.get_plugin_settings(sub.store)
            grace_days = grace_days or plugin_settings["grace_period_days"]

            end_limit = sub.expires_at or sub.current_period_end
            grace_end = end_limit + timedelta(days=grace_days)

            if sub.status == SubscriptionStatus.CANCELED and sub.expires_at and sub.expires_at > now:
                continue

            if now > grace_end:
                if sub.status != SubscriptionStatus.EXPIRED:
                    sub.status = SubscriptionStatus.EXPIRED
                    sub.expires_at = now
                    sub.save(update_fields=["status", "expires_at", "updated_at"])
                    expired_count += 1
            elif now > end_limit and sub.status == SubscriptionStatus.ACTIVE:
                sub.status = SubscriptionStatus.PAST_DUE
                sub.save(update_fields=["status", "updated_at"])

        return expired_count

    def refresh_status(self, subscription: CustomerSubscription) -> None:
        now = timezone.now()
        if subscription.status == SubscriptionStatus.TRIALING and subscription.trial_ends_at and now >= subscription.trial_ends_at:
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.current_period_end = self._add_interval(
                subscription.trial_ends_at, subscription.interval, subscription.interval_count,
            )
            subscription.save(update_fields=["status", "current_period_end", "updated_at"])

    def list_user_subscriptions(self, user, store):
        qs = CustomerSubscription.objects.filter(store=store, user=user).select_related("product", "plan")
        for sub in qs:
            self.refresh_status(sub)
        return qs.order_by("-created_at")

    def list_store_subscriptions(self, store, status: str | None = None):
        qs = CustomerSubscription.objects.filter(store=store).select_related("user", "product")
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")

    def user_has_access(self, user, store, product_id: int) -> bool:
        sub = CustomerSubscription.objects.filter(
            store=store,
            user=user,
            product_id=product_id,
            status__in=[SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE],
        ).first()
        if not sub:
            return False
        self.refresh_status(sub)
        return sub.status in (SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE)

    def serialize_subscription(self, sub: CustomerSubscription) -> dict:
        return {
            "id": sub.id,
            "product_id": sub.product_id,
            "product_name": sub.product.name,
            "status": sub.status,
            "status_label": sub.get_status_display(),
            "interval": sub.interval,
            "interval_label": sub.get_interval_display(),
            "interval_count": sub.interval_count,
            "price": str(int(sub.price)),
            "auto_renew": sub.auto_renew,
            "started_at": sub.started_at.isoformat(),
            "current_period_start": sub.current_period_start.isoformat(),
            "current_period_end": sub.current_period_end.isoformat(),
            "trial_ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
            "canceled_at": sub.canceled_at.isoformat() if sub.canceled_at else None,
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
            "renewal_count": sub.renewal_count,
            "is_active": sub.status in (SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE, SubscriptionStatus.PAST_DUE),
        }

    def serialize_plan(self, plan: SubscriptionPlan) -> dict:
        return {
            "id": plan.id,
            "product_id": plan.product_id,
            "interval": plan.interval,
            "interval_label": plan.get_interval_display(),
            "interval_count": plan.interval_count,
            "trial_days": plan.trial_days,
            "grace_period_days": plan.grace_period_days,
            "price": str(int(plan.price)),
            "is_active": plan.is_active,
        }

    def _add_interval(self, start, interval: str, count: int):
        count = max(1, count)
        if interval == BillingInterval.WEEKLY:
            return start + timedelta(weeks=count)
        if interval == BillingInterval.MONTHLY:
            return start + relativedelta(months=count)
        if interval == BillingInterval.YEARLY:
            return start + relativedelta(years=count)
        return start + relativedelta(months=count)
