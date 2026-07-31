"""CMS admin."""

from django.contrib import admin

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


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fk_name = "menu"


class ContentBlockInline(admin.TabularInline):
    model = ContentBlock
    extra = 1


class SlideInline(admin.TabularInline):
    model = Slide
    extra = 1


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "store", "slug", "is_published", "sort_order")
    list_filter = ("store", "is_published")
    search_fields = ("title", "slug")
    inlines = [ContentBlockInline]


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("store", "name", "location", "is_active")
    list_filter = ("location", "store")
    inlines = [MenuItemInline]


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "store", "position", "is_active", "sort_order")
    list_filter = ("position", "store", "is_active")


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "slug", "is_active")
    list_filter = ("store",)
    inlines = [SlideInline]


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ("name", "store", "slug", "widget_type", "is_active")
    list_filter = ("widget_type", "store")


@admin.register(LayoutSettings)
class LayoutSettingsAdmin(admin.ModelAdmin):
    list_display = ("store", "use_custom_header", "use_custom_footer")


@admin.register(Shortcode)
class ShortcodeAdmin(admin.ModelAdmin):
    list_display = ("name", "label", "store", "is_self_closing", "is_active")
    list_filter = ("store", "is_active", "is_self_closing")
    search_fields = ("name", "label")
