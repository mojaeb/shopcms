"""Blog admin."""

from django.contrib import admin

from blog.models import BlogCategory, BlogComment, BlogPost, BlogTag


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "is_active")
    list_filter = ("store",)


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ("name", "store")
    list_filter = ("store",)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "store", "category", "is_published", "published_at")
    list_filter = ("store", "is_published", "category")
    search_fields = ("title", "slug")
    filter_horizontal = ("tags",)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "status", "created_at")
    list_filter = ("store", "status")
