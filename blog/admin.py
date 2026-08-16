"""Blog admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from blog.models import BlogCategory, BlogComment, BlogPost, BlogTag


@admin.register(BlogCategory)
class BlogCategoryAdmin(ModelAdmin):
    list_display = ("name", "store", "is_active")
    list_filter = ("store",)


@admin.register(BlogTag)
class BlogTagAdmin(ModelAdmin):
    list_display = ("name", "store")
    list_filter = ("store",)


@admin.register(BlogPost)
class BlogPostAdmin(ModelAdmin):
    list_display = ("title", "store", "category", "is_published", "published_at")
    list_filter = ("store", "is_published", "category")
    search_fields = ("title", "slug")
    filter_horizontal = ("tags",)


@admin.register(BlogComment)
class BlogCommentAdmin(ModelAdmin):
    list_display = ("post", "user", "status", "created_at")
    list_filter = ("store", "status")
