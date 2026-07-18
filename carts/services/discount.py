"""Discount validation and calculation."""

import logging
from decimal import Decimal

from django.utils import timezone

from carts.enums import DiscountScope, DiscountType
from carts.models import Cart, Coupon, CouponUsage, GiftCard
from orders.enums import OrderStatus
from orders.models import Order
from tenants.models import StorePlugin

logger = logging.getLogger(__name__)


class DiscountError(Exception):
    pass


class DiscountService:
    """Advanced coupon and gift card logic."""

    PAID_STATUSES = [
        OrderStatus.PAID,
        OrderStatus.PREPARING,
        OrderStatus.SENT,
        OrderStatus.DELIVERED,
    ]

    def is_coupon_plugin_active(self, store) -> bool:
        from plugins.services.plugin import PluginService

        return PluginService().is_enabled(store, "coupon")

    def validate_coupon(self, cart: Cart, code: str, user=None) -> Coupon:
        if not self.is_coupon_plugin_active(cart.store):
            raise DiscountError("سیستم تخفیف فعال نیست")

        code = code.strip().upper()
        try:
            coupon = Coupon.objects.prefetch_related("categories", "products", "allowed_users").get(
                store=cart.store, code__iexact=code,
            )
        except Coupon.DoesNotExist:
            raise DiscountError("کوپن نامعتبر است")

        if not coupon.is_active:
            raise DiscountError("کوپن غیرفعال است")

        now = timezone.now()
        if coupon.valid_from and now < coupon.valid_from:
            raise DiscountError("کوپن هنوز فعال نشده است")
        if coupon.valid_until and now > coupon.valid_until:
            raise DiscountError("کوپن منقضی شده است")
        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            raise DiscountError("ظرفیت استفاده از کوپن تکمیل شده است")

        user = user or cart.user
        if coupon.first_purchase_only:
            if not user:
                raise DiscountError("این کوپن فقط برای کاربران واردشده است")
            if not self._is_first_purchase(user, cart.store):
                raise DiscountError("این کوپن فقط برای اولین خرید است")

        if coupon.allowed_users.exists():
            if not user or not coupon.allowed_users.filter(pk=user.pk).exists():
                raise DiscountError("شما مجاز به استفاده از این کوپن نیستید")

        if coupon.per_user_limit and user:
            usage_count = CouponUsage.objects.filter(coupon=coupon, user=user).count()
            if usage_count >= coupon.per_user_limit:
                raise DiscountError("سقف استفاده شما از این کوپن تکمیل شده است")

        subtotal = self._cart_subtotal(cart)
        if subtotal < coupon.min_order_amount:
            raise DiscountError(f"حداقل مبلغ سفارش برای این کوپن {coupon.min_order_amount} است")

        eligible = self._eligible_subtotal(cart, coupon)
        if eligible <= 0:
            raise DiscountError("هیچ محصولی برای این کوپن واجد شرایط نیست")

        return coupon

    def validate_gift_card(self, cart: Cart, code: str, user=None) -> GiftCard:
        if not self.is_coupon_plugin_active(cart.store):
            raise DiscountError("سیستم تخفیف فعال نیست")

        code = code.strip().upper()
        try:
            gift = GiftCard.objects.get(store=cart.store, code__iexact=code)
        except GiftCard.DoesNotExist:
            raise DiscountError("کارت هدیه نامعتبر است")

        if not gift.is_active:
            raise DiscountError("کارت هدیه غیرفعال است")
        if gift.balance <= 0:
            raise DiscountError("موجودی کارت هدیه تمام شده است")

        now = timezone.now()
        if gift.valid_until and now > gift.valid_until:
            raise DiscountError("کارت هدیه منقضی شده است")

        user = user or cart.user
        if gift.owner_id and (not user or gift.owner_id != user.pk):
            raise DiscountError("این کارت هدیه متعلق به شما نیست")

        return gift

    def calculate_discounts(self, cart: Cart) -> dict:
        subtotal = self._cart_subtotal(cart)
        coupon_discount = Decimal("0")
        gift_discount = Decimal("0")

        if cart.coupon_id:
            coupon_discount = self.calculate_coupon_discount(cart.coupon, cart)

        remaining = max(Decimal("0"), subtotal - coupon_discount)
        if cart.gift_card_id:
            gift_discount = min(cart.gift_card.balance, remaining)

        total_discount = coupon_discount + gift_discount
        total = max(Decimal("0"), subtotal - total_discount)

        return {
            "subtotal": subtotal,
            "coupon_discount": coupon_discount,
            "gift_discount": gift_discount,
            "discount": total_discount,
            "total": total,
            "item_count": sum(item.quantity for item in cart.items.all()),
        }

    def calculate_coupon_discount(self, coupon: Coupon, cart: Cart) -> Decimal:
        base = self._eligible_subtotal(cart, coupon)
        if base <= 0:
            return Decimal("0")

        if coupon.discount_type == DiscountType.PERCENTAGE:
            amount = (base * coupon.value) / Decimal("100")
            if coupon.max_discount_amount is not None:
                amount = min(amount, coupon.max_discount_amount)
            return min(amount, base)

        return min(coupon.value, base)

    def redeem_on_order(self, order, cart: Cart, user=None) -> None:
        totals = self.calculate_discounts(cart)
        user = user or cart.user

        if cart.coupon_id and totals["coupon_discount"] > 0:
            coupon = cart.coupon
            CouponUsage.objects.create(
                coupon=coupon,
                user=user,
                order=order,
                discount_amount=totals["coupon_discount"],
            )
            coupon.used_count += 1
            coupon.save(update_fields=["used_count", "updated_at"])

        if cart.gift_card_id and totals["gift_discount"] > 0:
            gift = cart.gift_card
            from carts.models import GiftCardUsage

            GiftCardUsage.objects.create(
                gift_card=gift,
                user=user,
                order=order,
                amount=totals["gift_discount"],
            )
            gift.balance -= totals["gift_discount"]
            gift.save(update_fields=["balance", "updated_at"])

    def serialize_coupon(self, coupon: Coupon) -> dict:
        return {
            "id": coupon.id,
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "value": str(int(coupon.value)),
            "scope": coupon.scope,
            "min_order_amount": str(int(coupon.min_order_amount)),
            "max_uses": coupon.max_uses,
            "used_count": coupon.used_count,
            "valid_from": coupon.valid_from.isoformat() if coupon.valid_from else None,
            "valid_until": coupon.valid_until.isoformat() if coupon.valid_until else None,
            "is_active": coupon.is_active,
            "first_purchase_only": coupon.first_purchase_only,
            "max_discount_amount": str(int(coupon.max_discount_amount)) if coupon.max_discount_amount else None,
            "per_user_limit": coupon.per_user_limit,
            "category_ids": list(coupon.categories.values_list("id", flat=True)),
            "product_ids": list(coupon.products.values_list("id", flat=True)),
            "allowed_user_ids": list(coupon.allowed_users.values_list("id", flat=True)),
        }

    def serialize_gift_card(self, gift: GiftCard) -> dict:
        return {
            "id": gift.id,
            "code": gift.code,
            "initial_balance": str(int(gift.initial_balance)),
            "balance": str(int(gift.balance)),
            "owner_id": gift.owner_id,
            "valid_until": gift.valid_until.isoformat() if gift.valid_until else None,
            "is_active": gift.is_active,
        }

    def _eligible_subtotal(self, cart: Cart, coupon: Coupon) -> Decimal:
        items = cart.items.select_related("product").all()
        if coupon.scope == DiscountScope.ALL:
            return sum(item.line_total for item in items)

        if coupon.scope == DiscountScope.CATEGORY:
            category_ids = set(coupon.categories.values_list("id", flat=True))
            return sum(item.line_total for item in items if item.product.category_id in category_ids)

        if coupon.scope == DiscountScope.PRODUCT:
            product_ids = set(coupon.products.values_list("id", flat=True))
            return sum(item.line_total for item in items if item.product_id in product_ids)

        return Decimal("0")

    def _cart_subtotal(self, cart: Cart) -> Decimal:
        return sum(item.line_total for item in cart.items.select_related("product").all())

    def _is_first_purchase(self, user, store) -> bool:
        return not Order.objects.filter(
            store=store,
            user=user,
            status__in=self.PAID_STATUSES,
        ).exists()
