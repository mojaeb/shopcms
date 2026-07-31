"""Seed Lona Center homepage CMS slider + banners with real web images."""

from django.core.management.base import BaseCommand

from cms.enums import BannerPosition
from cms.models import Banner, Slide, Slider
from cms.services.cache import CMSCacheService
from tenants.models import Store
from tenants.services.theme_settings import ThemeSettingsService

# Curated Unsplash images (phones / tablets / accessories) — stable CDN URLs
SLIDES = [
    {
        "title": "گوشی‌های پرچمدار",
        "subtitle": "سامسونگ، شیائومی و اپل با قیمت رقابتی",
        "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1600&q=80",
        "link": "/products/mobile/",
        "sort_order": 0,
    },
    {
        "title": "تبلت برای کار و سرگرمی",
        "subtitle": "گلکسی تب و مدل‌های روز بازار",
        "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=1600&q=80",
        "link": "/products/tablet/",
        "sort_order": 1,
    },
    {
        "title": "ایربادز و هندزفری",
        "subtitle": "صدای شفاف، اتصال پایدار",
        "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=1600&q=80",
        "link": "/products/handsfree/",
        "sort_order": 2,
    },
    {
        "title": "شارژ سریع همیشه همراه",
        "subtitle": "پاوربانک و شارژر اصل",
        "image": "https://images.unsplash.com/photo-1556656793-08538906a9f8?auto=format&fit=crop&w=1600&q=80",
        "link": "/products/powerbank/",
        "sort_order": 3,
    },
]

BANNERS_TOP = [
    {
        "title": "موبایل و تبلت",
        "subtitle": "جدیدترین مدل‌های بازار",
        "image": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=1000&q=80",
        "link": "/products/mobile/",
        "sort_order": 0,
    },
    {
        "title": "لوازم جانبی",
        "subtitle": "پاوربانک، شارژر، قاب و گلس",
        "image": "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?auto=format&fit=crop&w=1000&q=80",
        "link": "/products/powerbank/",
        "sort_order": 1,
    },
]

BANNERS_MID = [
    {
        "title": "قاب و محافظ صفحه",
        "subtitle": "مراقبت از گوشی شما",
        "image": "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?auto=format&fit=crop&w=1200&q=80",
        "link": "/products/cases/",
        "sort_order": 0,
    },
    {
        "title": "شارژر و کابل",
        "subtitle": "شارژ امن و سریع",
        "image": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=1200&q=80",
        "link": "/products/charger/",
        "sort_order": 1,
    },
]


class Command(BaseCommand):
    help = "پر کردن اسلایدر و بنرهای خانه لونا سنتر با تصاویر اینترنتی"

    def handle(self, *args, **options):
        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("فروشگاه shop1 پیدا نشد."))
            return

        slider, _ = Slider.objects.update_or_create(
            store=store,
            slug="home",
            defaults={
                "name": "اسلایدر خانه لونا سنتر",
                "autoplay": True,
                "interval": 5500,
                "is_active": True,
            },
        )
        slider.slides.all().delete()
        Slide.objects.bulk_create(
            [
                Slide(
                    slider=slider,
                    title=row["title"],
                    subtitle=row["subtitle"],
                    image=row["image"],
                    link=row["link"],
                    sort_order=row["sort_order"],
                    is_active=True,
                )
                for row in SLIDES
            ]
        )
        self.stdout.write(self.style.SUCCESS(f"اسلایدر خانه: {len(SLIDES)} اسلاید"))

        Banner.objects.filter(
            store=store,
            position__in=[BannerPosition.HOME_TOP, BannerPosition.HOME_MIDDLE],
        ).delete()

        for row in BANNERS_TOP:
            Banner.objects.create(
                store=store,
                title=row["title"],
                subtitle=row["subtitle"],
                image=row["image"],
                link=row["link"],
                position=BannerPosition.HOME_TOP,
                sort_order=row["sort_order"],
                is_active=True,
            )
        for row in BANNERS_MID:
            Banner.objects.create(
                store=store,
                title=row["title"],
                subtitle=row["subtitle"],
                image=row["image"],
                link=row["link"],
                position=BannerPosition.HOME_MIDDLE,
                sort_order=row["sort_order"],
                is_active=True,
            )
        self.stdout.write(self.style.SUCCESS("بنرهای بالا و وسط خانه به‌روز شد."))

        # Keep theme hero in sync as fallback (if CMS slider disabled)
        theme = ThemeSettingsService()
        cfg = theme.get_theme_settings(store)
        cfg["hero"] = {
            "slides": [
                {
                    "image": s["image"],
                    "thumbnail": s["image"],
                    "title": s["title"],
                    "text": s["subtitle"],
                    "button_text": "مشاهده",
                    "button_link": s["link"],
                    "background_color": "#0f766e",
                }
                for s in SLIDES
            ]
        }
        theme.update_theme_settings(store, cfg)

        CMSCacheService().invalidate_store(store)
        self.stdout.write(self.style.SUCCESS("کش CMS پاک شد — اسلایدرها آماده‌اند."))
