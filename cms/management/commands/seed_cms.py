"""Seed sample CMS content."""

from django.core.management.base import BaseCommand

from cms.enums import BannerPosition, MenuLocation
from cms.models import Banner, LayoutSettings, Menu, MenuItem, Page, Slide, Slider
from tenants.models import Store


class Command(BaseCommand):
    help = "Seed sample CMS content for development"

    def handle(self, *args, **options):
        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("Store shop1 not found. Run seed_store first."))
            return

        page, _ = Page.objects.get_or_create(
            store=store,
            slug="about",
            defaults={
                "title": "درباره ما",
                "content": "<p>فروشگاه نمونه ShopCMS</p>",
                "meta_title": "درباره ما",
                "meta_description": "معرفی فروشگاه",
                "is_published": True,
            },
        )

        contact_page, _ = Page.objects.get_or_create(
            store=store,
            slug="contact",
            defaults={
                "title": "تماس با ما",
                "content": "<p>برای ارتباط با ما از این صفحه استفاده کنید.</p>",
                "meta_title": "تماس با ما",
                "meta_description": "راه‌های ارتباطی",
                "is_published": True,
            },
        )

        header_menu, _ = Menu.objects.get_or_create(
            store=store,
            location=MenuLocation.HEADER,
            defaults={"name": "Header Menu", "is_active": True},
        )
        default_items = [
            ("خانه", "/", 0),
            ("محصولات", "/category/", 1),
            ("درباره ما", f"/page/{page.slug}/", 2),
            ("تماس با ما", f"/page/{contact_page.slug}/", 3),
            ("وبلاگ", "/blog/", 4),
        ]
        for label, url, order in default_items:
            MenuItem.objects.get_or_create(
                menu=header_menu,
                label=label,
                defaults={"url": url, "sort_order": order},
            )

        Banner.objects.get_or_create(
            store=store,
            title="فروش ویژه",
            defaults={
                "subtitle": "تا ۳۰٪ تخفیف",
                "image": "https://placehold.co/1200x400/667eea/white?text=Sale",
                "link": "/category/",
                "position": BannerPosition.HOME_TOP,
                "sort_order": 0,
                "is_active": True,
            },
        )

        slider, _ = Slider.objects.get_or_create(
            store=store,
            slug="home",
            defaults={"name": "Home Slider", "autoplay": True, "interval": 5000, "is_active": True},
        )
        Slide.objects.get_or_create(
            slider=slider,
            title="اسلاید ۱",
            defaults={
                "subtitle": "محصولات جدید",
                "image": "https://placehold.co/1200x500/764ba2/white?text=Slide+1",
                "link": "/category/",
                "sort_order": 0,
            },
        )

        LayoutSettings.objects.get_or_create(store=store)

        self.stdout.write(self.style.SUCCESS("CMS seed data created successfully."))
