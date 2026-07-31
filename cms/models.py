"""CMS models."""

from django.db import models
from django.utils import timezone

from cms.enums import BannerPosition, BlockType, MenuLocation, WidgetType
from core.models import TimeStampedModel
from tenants.models import Store


class SeoFieldsMixin(models.Model):
    """Reusable SEO fields."""

    meta_title = models.CharField(max_length=200, blank=True, verbose_name="عنوان SEO")
    meta_description = models.CharField(max_length=500, blank=True, verbose_name="توضیح SEO")
    meta_keywords = models.CharField(max_length=500, blank=True, verbose_name="کلمات کلیدی")
    og_image = models.URLField(blank=True, verbose_name="تصویر Open Graph")
    canonical_url = models.URLField(blank=True, verbose_name="URL کانونیکال")
    robots = models.CharField(max_length=100, default="index,follow", verbose_name="Robots")
    head_scripts = models.TextField(blank=True, verbose_name="اسکریپت Head")
    footer_scripts = models.TextField(blank=True, verbose_name="اسکریپت Footer")

    class Meta:
        abstract = True


class LayoutSettings(TimeStampedModel):
    """Store-level header/footer HTML overrides."""

    store = models.OneToOneField(
        Store,
        on_delete=models.CASCADE,
        related_name="layout_settings",
        verbose_name="فروشگاه",
    )
    header_html = models.TextField(blank=True, verbose_name="HTML هدر")
    footer_html = models.TextField(blank=True, verbose_name="HTML فوتر")
    use_custom_header = models.BooleanField(default=False, verbose_name="هدر سفارشی")
    use_custom_footer = models.BooleanField(default=False, verbose_name="فوتر سفارشی")

    class Meta:
        verbose_name = "تنظیمات چیدمان"
        verbose_name_plural = "تنظیمات چیدمان"


class Page(TimeStampedModel, SeoFieldsMixin):
    """CMS static page."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="pages", verbose_name="فروشگاه")
    title = models.CharField(max_length=200, verbose_name="عنوان")
    slug = models.SlugField(max_length=200, verbose_name="شناسه")
    content = models.TextField(blank=True, verbose_name="محتوا")
    template = models.CharField(max_length=100, blank=True, verbose_name="قالب")
    is_published = models.BooleanField(default=True, verbose_name="منتشر شده")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انتشار")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        verbose_name = "صفحه"
        verbose_name_plural = "صفحات"
        unique_together = [("store", "slug")]
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class Menu(TimeStampedModel):
    """Navigation menu container."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="menus", verbose_name="فروشگاه")
    name = models.CharField(max_length=100, verbose_name="نام")
    location = models.CharField(max_length=20, choices=MenuLocation.choices, verbose_name="مکان")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "منو"
        verbose_name_plural = "منوها"
        unique_together = [("store", "location")]
        ordering = ["location"]

    def __str__(self):
        return f"{self.store.slug} - {self.get_location_display()}"


class MenuItem(TimeStampedModel):
    """Menu item with optional nesting."""

    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="items", verbose_name="منو")
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="والد",
    )
    label = models.CharField(max_length=100, verbose_name="برچسب")
    url = models.CharField(max_length=500, blank=True, verbose_name="لینک")
    page = models.ForeignKey(
        Page,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="menu_items",
        verbose_name="صفحه",
    )
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    open_new_tab = models.BooleanField(default=False, verbose_name="تب جدید")

    class Meta:
        verbose_name = "آیتم منو"
        verbose_name_plural = "آیتم‌های منو"
        ordering = ["sort_order", "label"]

    def __str__(self):
        return self.label

    @property
    def href(self) -> str:
        if self.page:
            return f"/page/{self.page.slug}/"
        return self.url or "#"


class Banner(TimeStampedModel, SeoFieldsMixin):
    """Promotional banner."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="banners", verbose_name="فروشگاه")
    title = models.CharField(max_length=200, verbose_name="عنوان")
    subtitle = models.CharField(max_length=300, blank=True, verbose_name="زیرعنوان")
    image = models.URLField(blank=True, verbose_name="تصویر")
    link = models.CharField(max_length=500, blank=True, verbose_name="لینک")
    position = models.CharField(max_length=30, choices=BannerPosition.choices, verbose_name="موقعیت")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    starts_at = models.DateTimeField(null=True, blank=True, verbose_name="شروع")
    ends_at = models.DateTimeField(null=True, blank=True, verbose_name="پایان")

    class Meta:
        verbose_name = "بنر"
        verbose_name_plural = "بنرها"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_visible(self) -> bool:
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True


class Slider(TimeStampedModel):
    """Image slider container."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="sliders", verbose_name="فروشگاه")
    name = models.CharField(max_length=100, verbose_name="نام")
    slug = models.SlugField(max_length=100, verbose_name="شناسه")
    autoplay = models.BooleanField(default=True, verbose_name="پخش خودکار")
    interval = models.PositiveIntegerField(default=5000, verbose_name="فاصله (ms)")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "اسلایدر"
        verbose_name_plural = "اسلایدرها"
        unique_together = [("store", "slug")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class Slide(TimeStampedModel):
    """Single slide in a slider."""

    slider = models.ForeignKey(Slider, on_delete=models.CASCADE, related_name="slides", verbose_name="اسلایدر")
    title = models.CharField(max_length=200, blank=True, verbose_name="عنوان")
    subtitle = models.CharField(max_length=300, blank=True, verbose_name="زیرعنوان")
    image = models.URLField(verbose_name="تصویر")
    link = models.CharField(max_length=500, blank=True, verbose_name="لینک")
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "اسلاید"
        verbose_name_plural = "اسلایدها"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title or f"Slide {self.id}"


class Widget(TimeStampedModel):
    """Reusable content widget."""

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="widgets", verbose_name="فروشگاه")
    name = models.CharField(max_length=100, verbose_name="نام")
    slug = models.SlugField(max_length=100, verbose_name="شناسه")
    widget_type = models.CharField(max_length=30, choices=WidgetType.choices, default=WidgetType.HTML, verbose_name="نوع")
    content = models.JSONField(default=dict, verbose_name="محتوا")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "ویجت"
        verbose_name_plural = "ویجت‌ها"
        unique_together = [("store", "slug")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class ContentBlock(TimeStampedModel):
    """Page content block."""

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="blocks", verbose_name="صفحه")
    block_type = models.CharField(max_length=20, choices=BlockType.choices, default=BlockType.TEXT, verbose_name="نوع")
    title = models.CharField(max_length=200, blank=True, verbose_name="عنوان")
    content = models.JSONField(default=dict, verbose_name="محتوا")
    widget = models.ForeignKey(
        Widget,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blocks",
        verbose_name="ویجت",
    )
    sort_order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "بلوک محتوا"
        verbose_name_plural = "بلوک‌های محتوا"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title or f"Block {self.id}"


class Shortcode(TimeStampedModel):
    """Store-defined shortcode template (overrides builtins when names match)."""

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="shortcodes",
        verbose_name="فروشگاه",
    )
    name = models.SlugField(max_length=50, verbose_name="نام shortcode")
    label = models.CharField(max_length=100, verbose_name="برچسب")
    description = models.CharField(max_length=500, blank=True, verbose_name="توضیحات")
    html_template = models.TextField(
        verbose_name="قالب HTML",
        help_text="از {{content}} و {{نام_ویژگی}} استفاده کنید",
    )
    is_self_closing = models.BooleanField(default=False, verbose_name="بدون تگ پایانی")
    example = models.TextField(blank=True, verbose_name="مثال")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "شورت‌کد"
        verbose_name_plural = "شورت‌کدها"
        unique_together = [("store", "name")]
        ordering = ["name"]

    def __str__(self):
        return f"[{self.name}]"
