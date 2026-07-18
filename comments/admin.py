"""Comment admin."""

from django.contrib import admin

from comments.models import Comment, CommentLike


class ReplyInline(admin.TabularInline):
    model = Comment
    fk_name = "parent"
    extra = 0
    readonly_fields = ("user", "body", "status")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "status", "likes_count", "is_verified_purchase", "created_at")
    list_filter = ("store", "status", "rating")
    search_fields = ("body", "user__phone", "product__name")
    inlines = [ReplyInline]


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ("comment", "user", "created_at")
