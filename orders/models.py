"""Order models."""

import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimeStampedModel
from orders.enums import OrderStatus, ShipmentStatus
from tenants.models import Store


def generate_order_number() -> str:
    return f"ORD-{secrets.token_hex(4).upper()}"


class Order(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="orders", verbose_name="فروشگاه")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="کاربر",
    )
    order_number = models.CharField(max_length=32, verbose_name="شماره سفارش")
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.WAITING_PAYMENT,
        verbose_name="وضعیت",
    )
    payment = models.OneToOneField(
        "payments.PaymentTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order",
        verbose_name="پرداخت",
    )
    address_snapshot = models.JSONField(default=dict, blank=True, verbose_name="آدرس")
    shipping_method = models.CharField(max_length=200, blank=True, verbose_name="روش ارسال")
    shipping_provider = models.CharField(max_length=50, blank=True, verbose_name="ارائه‌دهنده ارسال")
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="جمع جزء")
    discount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="تخفیف")
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="هزینه ارسال")
    tax = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مالیات")
    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="جمع کل")
    coupon_code = models.CharField(max_length=50, blank=True, verbose_name="کد کوپن")
    gift_card_code = models.CharField(max_length=50, blank=True, verbose_name="کد کارت هدیه")
    customer_note = models.TextField(blank=True, verbose_name="یادداشت مشتری")

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"
        unique_together = [("store", "order_number")]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["store", "created_at"]),
            models.Index(fields=["store", "user"]),
        ]

    def __str__(self):
        return self.order_number


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="سفارش")
    product_id = models.IntegerField(verbose_name="شناسه محصول")
    product_name = models.CharField(max_length=300, verbose_name="نام محصول")
    product_slug = models.CharField(max_length=300, blank=True, verbose_name="شناسه محصول")
    variant_id = models.IntegerField(null=True, blank=True, verbose_name="شناسه تنوع")
    variant_label = models.CharField(max_length=200, blank=True, verbose_name="برچسب تنوع")
    sku = models.CharField(max_length=100, blank=True, verbose_name="SKU")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="تعداد")
    unit_price = models.DecimalField(max_digits=12, decimal_places=0, validators=[MinValueValidator(0)], verbose_name="قیمت واحد")
    line_total = models.DecimalField(max_digits=12, decimal_places=0, validators=[MinValueValidator(0)], verbose_name="جمع خط")
    image = models.URLField(blank=True, verbose_name="تصویر")

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


class Shipment(TimeStampedModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="shipment", verbose_name="سفارش")
    status = models.CharField(
        max_length=20,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.PENDING,
        verbose_name="وضعیت",
    )
    tracking_code = models.CharField(max_length=100, blank=True, verbose_name="کد رهگیری")
    carrier = models.CharField(max_length=100, blank=True, verbose_name="حامل")
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان ارسال")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تحویل")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="متادیتا")

    class Meta:
        verbose_name = "مرسوله"
        verbose_name_plural = "مرسوله‌ها"

    def __str__(self):
        return f"{self.order.order_number} - {self.tracking_code or self.status}"


class OrderHistory(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history", verbose_name="سفارش")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, verbose_name="وضعیت")
    note = models.TextField(blank=True, verbose_name="یادداشت")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_history_entries",
        verbose_name="کاربر",
    )

    class Meta:
        verbose_name = "تاریخچه سفارش"
        verbose_name_plural = "تاریخچه سفارشات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"


class Invoice(TimeStampedModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice", verbose_name="سفارش")
    invoice_number = models.CharField(max_length=32, unique=True, verbose_name="شماره فاکتور")
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ صدور")
    pdf_url = models.URLField(blank=True, verbose_name="آدرس PDF")

    class Meta:
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها"

    def __str__(self):
        return self.invoice_number
