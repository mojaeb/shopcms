"""Cart models."""

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from carts.enums import DiscountScope, DiscountType
from core.models import TimeStampedModel
from products.models import Product, ProductVariant
from tenants.models import Store


class Cart(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="carts", verbose_name="فروشگاه")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carts",
        verbose_name="کاربر",
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True, verbose_name="کلید نشست")
    coupon = models.ForeignKey(
        "Coupon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
        verbose_name="کوپن",
    )
    gift_card = models.ForeignKey(
        "GiftCard",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
        verbose_name="کارت هدیه",
    )

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"
        constraints = [
            models.UniqueConstraint(
                fields=["store", "user"],
                condition=Q(user__isnull=False),
                name="unique_cart_per_user_store",
            ),
            models.UniqueConstraint(
                fields=["store", "session_key"],
                condition=Q(user__isnull=True) & ~Q(session_key=""),
                name="unique_cart_per_session_store",
            ),
        ]

    def __str__(self):
        if self.user_id:
            return f"Cart #{self.pk} - {self.user}"
        return f"Cart #{self.pk} - guest:{self.session_key[:8]}"


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="سبد")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items", verbose_name="محصول")
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart_items",
        verbose_name="تنوع",
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="تعداد")
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت واحد",
    )

    class Meta:
        verbose_name = "آیتم سبد"
        verbose_name_plural = "آیتم‌های سبد"
        unique_together = [("cart", "product", "variant")]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class Coupon(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="coupons", verbose_name="فروشگاه")
    code = models.CharField(max_length=50, verbose_name="کد")
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
        verbose_name="نوع تخفیف",
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="مقدار",
    )
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="حداقل سفارش",
    )
    max_uses = models.PositiveIntegerField(null=True, blank=True, verbose_name="حداکثر استفاده")
    used_count = models.PositiveIntegerField(default=0, verbose_name="تعداد استفاده")
    valid_from = models.DateTimeField(null=True, blank=True, verbose_name="شروع اعتبار")
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name="پایان اعتبار")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    first_purchase_only = models.BooleanField(default=False, verbose_name="فقط اولین خرید")
    scope = models.CharField(
        max_length=20,
        choices=DiscountScope.choices,
        default=DiscountScope.ALL,
        verbose_name="محدوده",
    )
    max_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="سقف تخفیف",
    )
    per_user_limit = models.PositiveIntegerField(null=True, blank=True, verbose_name="حداکثر استفاده هر کاربر")
    categories = models.ManyToManyField(
        "products.Category",
        blank=True,
        related_name="coupons",
        verbose_name="دسته‌بندی‌ها",
    )
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="coupons",
        verbose_name="محصولات",
    )
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="exclusive_coupons",
        verbose_name="کاربران مجاز",
    )

    class Meta:
        verbose_name = "کوپن"
        verbose_name_plural = "کوپن‌ها"
        unique_together = [("store", "code")]
        ordering = ["-created_at"]

    def __str__(self):
        return self.code


class GiftCard(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="gift_cards", verbose_name="فروشگاه")
    code = models.CharField(max_length=50, verbose_name="کد")
    initial_balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="موجودی اولیه",
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="موجودی",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gift_cards",
        verbose_name="مالک",
    )
    valid_until = models.DateTimeField(null=True, blank=True, verbose_name="پایان اعتبار")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "کارت هدیه"
        verbose_name_plural = "کارت‌های هدیه"
        unique_together = [("store", "code")]
        ordering = ["-created_at"]

    def __str__(self):
        return self.code


class CouponUsage(TimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages", verbose_name="کوپن")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_usages",
        verbose_name="کاربر",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_usages",
        verbose_name="سفارش",
    )
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ تخفیف")

    class Meta:
        verbose_name = "استفاده از کوپن"
        verbose_name_plural = "استفاده‌های کوپن"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.coupon.code} - {self.user_id}"


class GiftCardUsage(TimeStampedModel):
    gift_card = models.ForeignKey(GiftCard, on_delete=models.CASCADE, related_name="usages", verbose_name="کارت هدیه")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gift_card_usages",
        verbose_name="کاربر",
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gift_card_usages",
        verbose_name="سفارش",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ")

    class Meta:
        verbose_name = "استفاده از کارت هدیه"
        verbose_name_plural = "استفاده‌های کارت هدیه"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.gift_card.code} - {self.amount}"
