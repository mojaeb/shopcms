"""CMS admin."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from cms.models import (
    Banner,
    ContentBlock,
    LayoutSettings,
    Menu,
    MenuItem,
    Page,
    Shortcode,
    Slide,
    Slider,
    Widget,
)


class MenuItemInline(TabularInline):
    model = MenuItem
    extra = 1
    fk_name = "menu"


class ContentBlockInline(TabularInline):
    model = ContentBlock
    extra = 1


class SlideInline(TabularInline):
    model = Slide
    extra = 1


@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ("title", "store", "slug", "is_published", "sort_order")
    list_filter = ("store", "is_published")
    search_fields = ("title", "slug")
    inlines = [ContentBlockInline]


@admin.register(Menu)
class MenuAdmin(ModelAdmin):
    list_display = ("store", "name", "location", "is_active")
    list_filter = ("location", "store")
    inlines = [MenuItemInline]


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    list_display = ("title", "store", "position", "is_active", "sort_order")
    list_filter = ("position", "store", "is_active")


@admin.register(Slider)
class SliderAdmin(ModelAdmin):
    list_display = ("name", "store", "slug", "is_active")
    list_filter = ("store",)
    inlines = [SlideInline]


@admin.register(Widget)
class WidgetAdmin(ModelAdmin):
    list_display = ("name", "store", "slug", "widget_type", "is_active")
    list_filter = ("widget_type", "store")


@admin.register(LayoutSettings)
class LayoutSettingsAdmin(ModelAdmin):
    list_display = ("store", "use_custom_header", "use_custom_footer")


@admin.register(Shortcode)
class ShortcodeAdmin(ModelAdmin):
    list_display = ("name", "label", "store", "is_self_closing", "is_active")
    list_filter = ("store", "is_active", "is_self_closing")
    search_fields = ("name", "label")
