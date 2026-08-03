"""Seed Gohar jewelry store — theme, domain, catalog, pages, menus from reference site."""

from __future__ import annotations

import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from cms.enums import MenuLocation
from cms.models import Menu, MenuItem, Page, Slide, Slider
from cms.services.cache import CMSCacheService
from cms.services.shortcodes import invalidate_shortcode_cache
from products.enums import ProductStatus, ProductType
from products.models import Brand, Category, Inventory, Product, ProductImage, Tag
from tenants.models import Domain, Store, Theme
from tenants.services.theme_settings import ThemeSettingsService

BASE = Path(settings.BASE_DIR)
SRC_IMAGES = BASE / "_temp" / "modern-jewelry-website" / "public" / "images"
DST_MEDIA = Path(settings.MEDIA_ROOT) / "gohar"
DST_STATIC = BASE / "static" / "themes" / "gohar" / "images"

IMAGE_FILES = (
    "atelier.png",
    "bracelet.png",
    "earrings.png",
    "hero-necklace.png",
    "necklace.png",
    "ring.png",
    "set.png",
    "watch.png",
)

ABOUT_HTML = """
<section class="gh-cms-hero">
  <div class="gh-cms-hero-bg">
    <img src="/media/gohar/atelier.png" alt="آتلیه گوهر">
    <div class="gh-cms-hero-veil"></div>
  </div>
  <div class="gh-width gh-cms-hero-copy">
    <p class="gh-kicker">OUR STORY</p>
    <h1 class="gh-title" style="font-size:clamp(2.5rem,6vw,4.5rem);max-width:48rem;">
      میراثی از <span class="text-gold-grad">هنر و اصالت</span>
    </h1>
    <p style="margin-top:1.75rem;color:rgb(244 239 230 / 0.7);max-width:36rem;line-height:1.85;font-size:1.1rem;">
      گوهر از سال ۱۳۶۵ با یک باور ساده آغاز شد: هر جواهر باید داستانی برای گفتن داشته باشد.
    </p>
  </div>
</section>

<section class="gh-width" style="padding:7rem 0;text-align:center;max-width:56rem;margin-inline:auto;">
  <h2 class="gh-title" style="font-size:clamp(1.75rem,3vw,2.5rem);line-height:1.7;">
    ما باور داریم که زیبایی واقعی در
    <span class="text-gold-grad">جزئیات</span>
    نهفته است و هر قطعه باید با
    <span class="text-gold-grad">دست</span>
    و عشق ساخته شود.
  </h2>
</section>

<section class="gh-width" style="padding-bottom:7rem;">
  <div class="gh-values-grid">
    <div class="gh-value-card card-hover">
      <div class="gh-value-icon">◆</div>
      <h3>اصالت</h3>
      <p>هر قطعه با گواهی اصالت و خلوص ارائه می‌شود؛ اعتماد شما سرمایه‌ی ماست.</p>
    </div>
    <div class="gh-value-card card-hover">
      <div class="gh-value-icon">✦</div>
      <h3>هنر دست</h3>
      <p>استادکاران ما با سال‌ها تجربه، هر طرح را به اثری منحصربه‌فرد بدل می‌کنند.</p>
    </div>
    <div class="gh-value-card card-hover">
      <div class="gh-value-icon">❖</div>
      <h3>پایداری</h3>
      <p>منابع ما اخلاقی و مسئولانه تأمین می‌شوند، چون به آینده اهمیت می‌دهیم.</p>
    </div>
  </div>
</section>

<section class="gh-timeline">
  <div class="gh-width" style="max-width:56rem;padding:7rem 0;">
    <h2 class="gh-title" style="text-align:center;margin-bottom:5rem;">مسیر گوهر</h2>
    <div class="gh-timeline-list">
      <div class="gh-timeline-row">
        <span class="gh-timeline-year">۱۳۶۵</span>
        <p>گشایش نخستین کارگاه کوچک گوهر در بازار تهران.</p>
      </div>
      <div class="gh-timeline-row">
        <span class="gh-timeline-year">۱۳۷۸</span>
        <p>راه‌اندازی آتلیه طراحی اختصاصی و آغاز همکاری با طراحان بین‌المللی.</p>
      </div>
      <div class="gh-timeline-row">
        <span class="gh-timeline-year">۱۳۹۲</span>
        <p>افتتاح بوتیک اصلی در خیابان ولیعصر و دریافت نشان کیفیت برتر.</p>
      </div>
      <div class="gh-timeline-row">
        <span class="gh-timeline-year">۱۴۰۳</span>
        <p>عرضه‌ی مجموعه آنلاین و دسترسی گوهر برای علاقه‌مندان در سراسر کشور.</p>
      </div>
    </div>
  </div>
</section>

<section class="gh-width gh-cta-band">
  <h2 class="gh-title">به خانواده گوهر بپیوندید</h2>
  <a href="/products/" class="btn-gold" style="display:inline-flex;margin-top:1.75rem;padding:1rem 2.5rem;">کاوش مجموعه</a>
</section>
""".strip()

CONTACT_HTML = """
<section class="gh-width" style="padding-top:2rem;">
  <p class="gh-kicker" style="letter-spacing:0.4em;margin-bottom:1.25rem;">CONTACT</p>
  <h1 class="gh-title" style="font-size:clamp(2.5rem,5vw,3.75rem);margin-bottom:1.5rem;">با ما در ارتباط باشید</h1>
  <p style="color:rgb(244 239 230 / 0.7);max-width:36rem;line-height:1.85;">
    برای مشاوره خرید، سفارش طرح اختصاصی یا هر پرسشی، کارشناسان گوهر آماده‌ی پاسخگویی هستند.
  </p>
</section>

<section class="gh-width gh-contact-grid">
  <div class="gh-contact-form-panel">
    <p style="color:var(--color-muted);line-height:1.8;margin:0 0 1.5rem;">
      پیام خود را از طریق فرم تماس پنل مدیریت یا ایمیل زیر ارسال کنید؛ به‌زودی پاسخ می‌دهیم.
    </p>
    <a href="mailto:info@gohar.ir" class="btn-gold" style="display:inline-flex;padding:1rem 2rem;">ارسال ایمیل</a>
  </div>
  <div class="gh-contact-info">
    <div class="gh-contact-card">
      <p class="gh-kicker" style="font-size:0.7rem;margin-bottom:0.75rem;">آدرس بوتیک</p>
      <p>تهران، خیابان ولیعصر، نبش کوچه گوهر، پلاک ۱۲</p>
    </div>
    <div class="gh-contact-card">
      <p class="gh-kicker" style="font-size:0.7rem;margin-bottom:0.75rem;">تلفن</p>
      <p dir="ltr" style="text-align:right;">۰۲۱ ۲۲۱۳ ۴۵۶۷</p>
    </div>
    <div class="gh-contact-card">
      <p class="gh-kicker" style="font-size:0.7rem;margin-bottom:0.75rem;">ایمیل</p>
      <p>info@gohar.ir</p>
    </div>
    <div class="gh-contact-card">
      <p class="gh-kicker" style="font-size:0.7rem;margin-bottom:0.75rem;">ساعات کاری</p>
      <p>شنبه تا پنج‌شنبه، ۱۰ تا ۲۰</p>
    </div>
  </div>
</section>

<section class="gh-width" style="padding:4rem 0 2rem;text-align:center;border-top:1px solid var(--color-line);margin-top:5rem;">
  <p style="color:var(--color-muted);max-width:40rem;margin:0 auto;line-height:1.8;">
    مایلید از نزدیک مجموعه را ببینید؟ برای بازدید حضوری و مشاوره‌ی تخصصی، یک وقت ملاقات رزرو کنید.
  </p>
  <a href="tel:+982122134567" class="btn-ghost" style="display:inline-flex;margin-top:2rem;padding:1rem 2.5rem;">رزرو وقت بازدید</a>
</section>
""".strip()


def media_url(*parts: str) -> str:
    return "/media/" + "/".join(parts)


# Home hero slides — CMS Slider(slug=home) + theme_settings.hero.slides sync
HERO_SLIDES = (
    {
        "title": "درخششی که جاودانه می‌ماند",
        "subtitle": "هر قطعه‌ی گوهر، حاصل ساعت‌ها هنر دست استادکاران ایرانی است؛ جواهراتی که میراث شما خواهند بود.",
        "image": "hero-necklace.png",
        "link": "/products/",
        "button_text": "مشاهده مجموعه",
        "kicker": "GOHAR · از سال ۱۳۶۵",
        "sort_order": 0,
    },
    {
        "title": "انگشترهایی برای عهد جاودان",
        "subtitle": "از سولیتر کلاسیک تا طرح‌های معاصر؛ هر انگشتر داستانی از عشق و اصالت را روایت می‌کند.",
        "image": "ring.png",
        "link": "/products/ring/",
        "button_text": "کاوش انگشترها",
        "kicker": "RINGS · انگشتر",
        "sort_order": 1,
    },
    {
        "title": "گردنبندهایی از نور و طلا",
        "subtitle": "آویزهای الماس و یاقوت، طراحی‌شده برای لحظه‌هایی که باید تا ابد بدرخشند.",
        "image": "necklace.png",
        "link": "/products/necklace/",
        "button_text": "مشاهده گردنبندها",
        "kicker": "NECKLACES · گردنبند",
        "sort_order": 2,
    },
    {
        "title": "آتلیه عروس گوهر",
        "subtitle": "سرویس‌های اختصاصی عروس، ساخته‌شده در آتلیه گوهر برای روزی که داستان شما آغاز می‌شود.",
        "image": "set.png",
        "link": "/products/set/",
        "button_text": "سرویس عروس",
        "kicker": "BRIDAL · آتلیه",
        "sort_order": 3,
    },
)


class Command(BaseCommand):
    help = "ایجاد فروشگاه گوهر با تم، کاتالوگ و صفحات مطابق سایت مرجع"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-media",
            action="store_true",
            help="کپی تصاویر را رد کن",
        )

    def handle(self, *args, **options):
        theme = self._ensure_theme()
        store = self._ensure_store(theme)
        self._ensure_domains(store)

        if not options["skip_media"]:
            self._copy_media()

        self._brand_store(store)
        self._seed_home_slider(store)
        cats = self._seed_categories(store)
        brand = self._seed_brand(store)
        tags = self._seed_tags(store)
        created = self._seed_products(store, cats, brand, tags)
        self._seed_pages(store)
        self._seed_menus(store)

        CMSCacheService().invalidate_store(store)
        invalidate_shortcode_cache(store)

        self.stdout.write(
            self.style.SUCCESS(
                f"Gohar ready: store={store.slug} theme={theme.slug} "
                f"products={created} -> http://gohar.local:8000/"
            )
        )

    def _ensure_theme(self) -> Theme:
        theme, created = Theme.objects.get_or_create(
            slug="gohar",
            defaults={
                "name": "گوهر",
                "directory": "gohar",
                "description": "تم لوکس جواهرات گوهر — تاریک، طلایی، RTL با Vite و Tailwind",
                "is_active": True,
            },
        )
        if not created:
            theme.name = "گوهر"
            theme.directory = "gohar"
            theme.is_active = True
            theme.save(update_fields=["name", "directory", "is_active", "description"])
        self.stdout.write(("+" if created else "~") + f" theme {theme.slug}")
        return theme

    def _ensure_store(self, theme: Theme) -> Store:
        default_theme = Theme.objects.filter(is_default=True).first() or theme
        store, created = Store.objects.get_or_create(
            slug="gohar",
            defaults={
                "name": "گوهر",
                "store_type": "physical",
                "theme": theme,
                "default_theme": default_theme,
                "currency": "IRR",
                "status": "active",
                "tax_enabled": False,
                "language": "fa",
            },
        )
        store.name = "گوهر"
        store.theme = theme
        store.default_theme = default_theme
        store.status = "active"
        store.currency = "IRR"
        store.language = "fa"
        store.save()
        self.stdout.write(("+" if created else "~") + f" store {store.slug}")
        return store

    def _ensure_domains(self, store: Store) -> None:
        for domain_name, is_primary in (
            ("gohar.local", True),
            ("gohar.localhost", False),
        ):
            domain, created = Domain.objects.get_or_create(
                domain=domain_name,
                defaults={
                    "store": store,
                    "is_primary": is_primary,
                    "is_active": True,
                },
            )
            if domain.store_id != store.id:
                domain.store = store
            domain.is_primary = is_primary
            domain.is_active = True
            domain.save()
            self.stdout.write(("+" if created else "~") + f" domain {domain.domain}")

    def _copy_media(self) -> None:
        DST_MEDIA.mkdir(parents=True, exist_ok=True)
        DST_STATIC.mkdir(parents=True, exist_ok=True)
        if not SRC_IMAGES.exists():
            self.stdout.write(self.style.WARNING(f"منبع تصاویر یافت نشد: {SRC_IMAGES}"))
            return
        copied = 0
        for name in IMAGE_FILES:
            src = SRC_IMAGES / name
            if not src.is_file():
                continue
            shutil.copy2(src, DST_MEDIA / name)
            shutil.copy2(src, DST_STATIC / name)
            copied += 1
        self.stdout.write(self.style.SUCCESS(f"Media copied ({copied} files) -> {DST_MEDIA}"))

    def _brand_store(self, store: Store) -> None:
        theme = ThemeSettingsService()
        current = theme.get_theme_settings(store)
        current["logo"] = ""
        current["colors"] = {
            "primary": "#c9a24b",
            "background": "#0a0a0a",
            "text": "#f4efe6",
        }
        current["hero"] = {
            "slides": [
                {
                    "image": media_url("gohar", row["image"]),
                    "thumbnail": media_url("gohar", row["image"]),
                    "title": row["title"],
                    "text": row["subtitle"],
                    "button_text": row["button_text"],
                    "button_link": row["link"],
                    "kicker": row["kicker"],
                    "background_color": "#0a0a0a",
                }
                for row in HERO_SLIDES
            ]
        }
        theme.update_theme_settings(store, current)
        self.stdout.write(
            self.style.SUCCESS(f"Gohar theme settings applied ({len(HERO_SLIDES)} hero slides).")
        )

    def _seed_home_slider(self, store: Store) -> None:
        slider, _ = Slider.objects.update_or_create(
            store=store,
            slug="home",
            defaults={
                "name": "اسلایدر خانه گوهر",
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
                    image=media_url("gohar", row["image"]),
                    link=row["link"],
                    sort_order=row["sort_order"],
                    is_active=True,
                )
                for row in HERO_SLIDES
            ]
        )
        self.stdout.write(self.style.SUCCESS(f"CMS home slider: {len(HERO_SLIDES)} slides"))

    def _seed_categories(self, store: Store) -> dict[str, Category]:
        # Home grid order: ring (tall), necklace, earring, bracelet (wide)
        specs = [
            ("ring", "انگشتر", "ring.png", 1, "RINGS"),
            ("necklace", "گردنبند", "necklace.png", 2, "NECKLACES"),
            ("earring", "گوشواره", "earrings.png", 3, "EARRINGS"),
            ("bracelet", "دستبند", "bracelet.png", 4, "BRACELETS"),
            ("watch", "ساعت", "watch.png", 5, "WATCHES"),
            ("set", "سرویس", "set.png", 6, "SETS"),
        ]
        out: dict[str, Category] = {}
        for slug, name, img, order, en in specs:
            cat, created = Category.objects.update_or_create(
                store=store,
                slug=slug,
                defaults={
                    "name": name,
                    "image": media_url("gohar", img),
                    "sort_order": order,
                    "is_active": True,
                    "description": f"مجموعه {name} گوهر — {en}",
                },
            )
            out[slug] = cat
            self.stdout.write(("+" if created else "~") + f" category {slug}")
        return out

    def _seed_brand(self, store: Store) -> Brand:
        brand, created = Brand.objects.get_or_create(
            store=store,
            slug="gohar",
            defaults={"name": "گوهر", "is_active": True},
        )
        self.stdout.write(("+" if created else "~") + f" brand {brand.slug}")
        return brand

    def _seed_tags(self, store: Store) -> dict[str, Tag]:
        out = {}
        for slug, name in (("new", "جدید"), ("featured", "ویژه")):
            tag, _ = Tag.objects.get_or_create(store=store, slug=slug, defaults={"name": name})
            out[slug] = tag
        return out

    def _seed_products(
        self,
        store: Store,
        cats: dict[str, Category],
        brand: Brand,
        tags: dict[str, Tag],
    ) -> int:
        # Mirror _temp/modern-jewelry-website/src/data.js
        catalog = [
            {
                "slug": "ring-solitaire",
                "name": "انگشتر سولیتر الماس",
                "cat": "ring",
                "price": 48500000,
                "img": "ring.png",
                "desc": "انگشتر طلای ۱۸ عیار با تک‌نگین الماس تراش برلیان، نماد سادگی و اصالت.",
                "featured": True,
            },
            {
                "slug": "necklace-ruby",
                "name": "گردنبند یاقوت سرخ",
                "cat": "necklace",
                "price": 32900000,
                "img": "necklace.png",
                "desc": "آویز ظریف طلا با یاقوت سرخ طبیعی، انتخابی گرم برای لحظه‌های خاص.",
                "featured": True,
            },
            {
                "slug": "earring-emerald",
                "name": "گوشواره زمرد آویز",
                "cat": "earring",
                "price": 27400000,
                "img": "earrings.png",
                "desc": "جفت گوشواره طلا با زمرد سبز، درخششی آرام و اشرافی.",
                "featured": True,
            },
            {
                "slug": "bracelet-tennis",
                "name": "دستبند تنیسی الماس",
                "cat": "bracelet",
                "price": 65000000,
                "img": "bracelet.png",
                "desc": "دستبند تمام‌الماس با ردیفی از نگین‌های هم‌اندازه، شکوه در حرکت.",
                "featured": True,
            },
            {
                "slug": "watch-gold",
                "name": "ساعت طلا نگین‌نشان",
                "cat": "watch",
                "price": 120000000,
                "img": "watch.png",
                "desc": "ساعت مچی طلا با قاب الماس‌نشان، تلفیق زمان و جواهر.",
                "featured": True,
            },
            {
                "slug": "set-bridal",
                "name": "سرویس عروس طلا",
                "cat": "set",
                "price": 185000000,
                "img": "set.png",
                "desc": "سرویس کامل عروس شامل گردنبند و گوشواره، طراحی به یادماندنی برای روز خاص.",
                "featured": True,
            },
            {
                "slug": "necklace-diamond",
                "name": "گردنبند الماس ریور",
                "cat": "necklace",
                "price": 98000000,
                "img": "hero-necklace.png",
                "desc": "گردنبند مجلسی با ردیف الماس‌های درخشان، شاهکار آتلیه گوهر.",
                "featured": False,
            },
            {
                "slug": "ring-emerald",
                "name": "انگشتر زمرد سلطنتی",
                "cat": "ring",
                "price": 54000000,
                "img": "earrings.png",
                "desc": "انگشتر طلا با زمرد مرکزی و حلقه‌ای از الماس، طراحی کلاسیک و فاخر.",
                "featured": False,
            },
        ]

        count = 0
        for row in catalog:
            cat = cats.get(row["cat"])
            product, created = Product.objects.update_or_create(
                store=store,
                slug=row["slug"],
                defaults={
                    "name": row["name"],
                    "short_description": row["desc"],
                    "description": (
                        f"<p>{row['desc']}</p>"
                        "<ul>"
                        "<li>طلای ۱۸ عیار با ضمانت اصالت</li>"
                        "<li>نگین‌های طبیعی با گواهی</li>"
                        "<li>ارسال رایگان و بسته‌بندی هدیه</li>"
                        "<li>امکان سفارش اختصاصی</li>"
                        "</ul>"
                    ),
                    "category": cat,
                    "brand": brand,
                    "product_type": ProductType.SIMPLE,
                    "status": ProductStatus.ACTIVE,
                    "base_price": Decimal(row["price"]),
                    "sku": f"GOH-{row['slug'].upper()}",
                    "is_featured": row["featured"],
                    "meta_title": f"{row['name']} | گوهر",
                    "meta_description": row["desc"],
                },
            )
            product.tags.set([tags["new"], tags["featured"]] if row["featured"] else [tags["new"]])

            img_url = media_url("gohar", row["img"])
            ProductImage.objects.update_or_create(
                product=product,
                is_primary=True,
                defaults={"image": img_url, "alt_text": row["name"], "sort_order": 0},
            )
            Inventory.objects.update_or_create(
                product=product,
                variant=None,
                defaults={"quantity": 5, "track_inventory": True},
            )
            count += 1
            self.stdout.write(("+" if created else "~") + f" product {product.slug}")
        return count

    def _seed_pages(self, store: Store) -> None:
        about, _ = Page.objects.update_or_create(
            store=store,
            slug="about",
            defaults={
                "title": "درباره ما",
                "content": ABOUT_HTML,
                "meta_title": "درباره گوهر | جواهرات لوکس دست‌ساز",
                "meta_description": "درباره گوهر؛ خانه‌ی جواهرات دست‌ساز ایرانی با بیش از سه دهه تجربه.",
                "is_published": True,
            },
        )
        contact, _ = Page.objects.update_or_create(
            store=store,
            slug="contact",
            defaults={
                "title": "تماس با ما",
                "content": CONTACT_HTML,
                "meta_title": "تماس با گوهر",
                "meta_description": "تماس با گوهر؛ مشاوره خرید، سفارش اختصاصی و آدرس بوتیک.",
                "is_published": True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Pages: /page/{about.slug}/ and /page/{contact.slug}/"))

    def _seed_menus(self, store: Store) -> None:
        header, _ = Menu.objects.get_or_create(
            store=store,
            location=MenuLocation.HEADER,
            defaults={"name": "منوی اصلی گوهر", "is_active": True},
        )
        header.name = "منوی اصلی گوهر"
        header.is_active = True
        header.save(update_fields=["name", "is_active"])

        # Wipe and recreate for clean reference order
        header.items.all().delete()
        for order, (label, url) in enumerate(
            (
                ("خانه", "/"),
                ("محصولات", "/products/"),
                ("درباره ما", "/page/about/"),
                ("تماس با ما", "/page/contact/"),
            ),
            start=1,
        ):
            MenuItem.objects.create(
                menu=header,
                label=label,
                url=url,
                sort_order=order,
                is_active=True,
            )

        footer, _ = Menu.objects.get_or_create(
            store=store,
            location=MenuLocation.FOOTER,
            defaults={"name": "منوی فوتر گوهر", "is_active": True},
        )
        footer.items.all().delete()
        for order, (label, url) in enumerate(
            (
                ("خانه", "/"),
                ("محصولات", "/products/"),
                ("درباره ما", "/page/about/"),
                ("تماس با ما", "/page/contact/"),
            ),
            start=1,
        ):
            MenuItem.objects.create(
                menu=footer,
                label=label,
                url=url,
                sort_order=order,
                is_active=True,
            )
        self.stdout.write(self.style.SUCCESS("Menus configured."))
