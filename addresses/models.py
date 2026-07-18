"""Address models."""

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from tenants.models import Store


class CustomerAddress(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="addresses", verbose_name="فروشگاه")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name="کاربر",
    )
    full_name = models.CharField(max_length=200, verbose_name="نام")
    phone = models.CharField(max_length=15, verbose_name="موبایل")
    province = models.CharField(max_length=100, verbose_name="استان")
    city = models.CharField(max_length=100, verbose_name="شهر")
    postal_code = models.CharField(max_length=10, verbose_name="کد پستی")
    address_line = models.TextField(verbose_name="آدرس")
    building_no = models.CharField(max_length=20, blank=True, verbose_name="پلاک")
    unit = models.CharField(max_length=20, blank=True, verbose_name="واحد")
    label = models.CharField(max_length=50, blank=True, verbose_name="برچسب")
    is_default = models.BooleanField(default=False, verbose_name="پیش‌فرض")

    class Meta:
        verbose_name = "آدرس مشتری"
        verbose_name_plural = "آدرس‌های مشتری"
        ordering = ["-is_default", "-updated_at"]

    def __str__(self):
        return f"{self.full_name} - {self.city}"

    @property
    def full_address(self) -> str:
        parts = [self.province, self.city, self.address_line]
        if self.building_no:
            parts.append(f"پلاک {self.building_no}")
        if self.unit:
            parts.append(f"واحد {self.unit}")
        return "، ".join(parts)
