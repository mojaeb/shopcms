"""Order enumerations."""

from django.db import models


class OrderStatus(models.TextChoices):
    PENDING = "pending", "در انتظار"
    WAITING_PAYMENT = "waiting_payment", "در انتظار پرداخت"
    PAID = "paid", "پرداخت شده"
    PREPARING = "preparing", "در حال آماده‌سازی"
    SENT = "sent", "ارسال شده"
    DELIVERED = "delivered", "تحویل شده"
    CANCELED = "canceled", "لغو شده"
    REFUNDED = "refunded", "بازگشت وجه"


class ShipmentStatus(models.TextChoices):
    PENDING = "pending", "در انتظار"
    PREPARING = "preparing", "آماده‌سازی"
    SHIPPED = "shipped", "ارسال شد"
    IN_TRANSIT = "in_transit", "در مسیر"
    DELIVERED = "delivered", "تحویل شد"
    RETURNED = "returned", "مرجوعی"
