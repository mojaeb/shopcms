"""Product models."""

from django.core.validators import MinValueValidator
from django.db import models

from cms.models import SeoFieldsMixin
from core.models import TimeStampedModel
from products.enums import AttributeDisplayType, ButtonDisplayStyle, ProductStatus, ProductType
from tenants.models import Store


class Tag(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="tags", verbose_name="فروشگاه")
    name = models.CharField(max_length=100, verbose_name="نام")
    slug = models.SlugField(max_length=100, verbose_name="شناسه")

    class Meta:
        verbose_name = "برچسب"
        verbose_name_plural = "برچسب‌ها"
        unique_together = [("store", "slug")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class Category(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="categories", verbose_name="فروشگاه")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="والد",
    )
    name = models.CharField(max_length=200, verbose_name="نام")
    slug = models.SlugField(max_length=200, verbose_name="شناسه")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    image = models.URLField(blank=True, verbose_name="تصویر")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        unique_together = [("store", "slug")]
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Brand(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="brands", verbose_name="فروشگاه")
    name = models.CharField(max_length=200, verbose_name="نام")
    slug = models.SlugField(max_length=200, verbose_name="شناسه")
    logo = models.URLField(blank=True, verbose_name="لوگو")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "برند"
        verbose_name_plural = "برندها"
        unique_together = [("store", "slug")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductAttribute(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="attributes", verbose_name="فروشگاه")
    name = models.CharField(max_length=100, verbose_name="نام")
    slug = models.SlugField(max_length=100, verbose_name="شناسه")
    display_type = models.CharField(
        max_length=20,
        choices=AttributeDisplayType.choices,
        default=AttributeDisplayType.SELECT,
        verbose_name="نوع نمایش",
    )
    button_style = models.CharField(
        max_length=20,
        choices=ButtonDisplayStyle.choices,
        blank=True,
        default="",
        verbose_name="سبک دکمه",
    )
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "ویژگی"
        verbose_name_plural = "ویژگی‌ها"
        unique_together = [("store", "slug")]
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class ProductAttributeValue(TimeStampedModel):
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name="ویژگی",
    )
    value = models.CharField(max_length=100, verbose_name="مقدار")
    slug = models.SlugField(max_length=100, verbose_name="شناسه")
    color_code = models.CharField(max_length=20, blank=True, verbose_name="کد رنگ")
    icon = models.URLField(blank=True, verbose_name="آیکون")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "مقدار ویژگی"
        verbose_name_plural = "مقادیر ویژگی"
        unique_together = [("attribute", "slug")]
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class Product(TimeStampedModel, SeoFieldsMixin):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products", verbose_name="فروشگاه")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="دسته‌بندی",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="برند",
    )
    name = models.CharField(max_length=300, verbose_name="نام")
    slug = models.SlugField(max_length=300, verbose_name="شناسه")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    short_description = models.CharField(max_length=500, blank=True, verbose_name="توضیح کوتاه")
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.SIMPLE,
        verbose_name="نوع",
    )
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        verbose_name="وضعیت",
    )
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت پایه",
    )
    compare_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت قبل تخفیف",
    )
    sku = models.CharField(max_length=100, blank=True, verbose_name="SKU")
    is_featured = models.BooleanField(default=False, verbose_name="ویژه")
    tags = models.ManyToManyField(Tag, blank=True, related_name="products", verbose_name="برچسب‌ها")

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        unique_together = [("store", "slug")]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["store", "status"]),
            models.Index(fields=["store", "created_at"]),
            models.Index(fields=["store", "base_price"]),
        ]

    def __str__(self):
        return self.name

    @property
    def is_active(self) -> bool:
        return self.status == ProductStatus.ACTIVE

    @property
    def primary_image(self) -> str:
        img = self.images.filter(is_primary=True).first() or self.images.first()
        return img.image if img else ""


class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants", verbose_name="محصول")
    sku = models.CharField(max_length=100, blank=True, verbose_name="SKU")
    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت",
    )
    compare_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت قبل تخفیف",
    )
    attributes = models.ManyToManyField(
        ProductAttributeValue,
        blank=True,
        related_name="variants",
        verbose_name="ویژگی‌ها",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "تنوع محصول"
        verbose_name_plural = "تنوع‌های محصول"
        ordering = ["id"]

    def __str__(self):
        return f"{self.product.name} - {self.sku or self.id}"


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", verbose_name="محصول")
    image = models.URLField(verbose_name="تصویر")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="متن جایگزین")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_primary = models.BooleanField(default=False, verbose_name="اصلی")

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصول"
        ordering = ["sort_order"]

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(
                is_primary=False
            )
        super().save(*args, **kwargs)


class ProductVideo(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="videos", verbose_name="محصول")
    url = models.URLField(verbose_name="آدرس ویدیو")
    title = models.CharField(max_length=200, blank=True, verbose_name="عنوان")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "ویدیو محصول"
        verbose_name_plural = "ویدیوهای محصول"
        ordering = ["sort_order"]


class Inventory(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="inventory_items",
        verbose_name="محصول",
    )
    variant = models.OneToOneField(
        ProductVariant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="inventory",
        verbose_name="تنوع",
    )
    quantity = models.IntegerField(default=0, verbose_name="موجودی")
    reserved = models.IntegerField(default=0, verbose_name="رزرو شده")
    low_stock_threshold = models.IntegerField(default=5, verbose_name="آستانه کمبود")
    track_inventory = models.BooleanField(default=True, verbose_name="پیگیری موجودی")

    class Meta:
        verbose_name = "موجودی"
        verbose_name_plural = "موجودی‌ها"

    @property
    def available(self) -> int:
        return max(0, self.quantity - self.reserved)

    @property
    def is_low_stock(self) -> bool:
        return self.track_inventory and self.available <= self.low_stock_threshold

    @property
    def is_in_stock(self) -> bool:
        if not self.track_inventory:
            return True
        return self.available > 0
