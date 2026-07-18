"""Blog models."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from cms.models import SeoFieldsMixin
from comments.enums import CommentStatus
from core.models import TimeStampedModel
from tenants.models import Store


class BlogCategory(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="blog_categories", verbose_name="فروشگاه")
    name = models.CharField(max_length=200, verbose_name="نام")
    slug = models.SlugField(max_length=200, verbose_name="شناسه")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "دسته وبلاگ"
        verbose_name_plural = "دسته‌های وبلاگ"
        unique_together = [("store", "slug")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class BlogTag(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="blog_tags", verbose_name="فروشگاه")
    name = models.CharField(max_length=100, verbose_name="نام")
    slug = models.SlugField(max_length=100, verbose_name="شناسه")

    class Meta:
        verbose_name = "برچسب وبلاگ"
        verbose_name_plural = "برچسب‌های وبلاگ"
        unique_together = [("store", "slug")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class BlogPost(TimeStampedModel, SeoFieldsMixin):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="blog_posts", verbose_name="فروشگاه")
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="دسته",
    )
    tags = models.ManyToManyField(BlogTag, blank=True, related_name="posts", verbose_name="برچسب‌ها")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
        verbose_name="نویسنده",
    )
    title = models.CharField(max_length=300, verbose_name="عنوان")
    slug = models.SlugField(max_length=300, verbose_name="شناسه")
    excerpt = models.TextField(blank=True, verbose_name="خلاصه")
    content = models.TextField(verbose_name="محتوا")
    featured_image = models.URLField(blank=True, verbose_name="تصویر شاخص")
    is_published = models.BooleanField(default=False, verbose_name="منتشر شده")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انتشار")

    class Meta:
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"
        unique_together = [("store", "slug")]
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class BlogComment(TimeStampedModel):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="blog_comments", verbose_name="فروشگاه")
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="comments", verbose_name="مقاله")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_comments",
        verbose_name="کاربر",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="پاسخ به",
    )
    body = models.TextField(verbose_name="متن")
    status = models.CharField(
        max_length=20,
        choices=CommentStatus.choices,
        default=CommentStatus.PENDING,
        verbose_name="وضعیت",
    )

    class Meta:
        verbose_name = "نظر وبلاگ"
        verbose_name_plural = "نظرات وبلاگ"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.post.title} - {self.user_id}"
