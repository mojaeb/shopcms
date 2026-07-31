"""Seed shop1 as Lona Center — موبایل، تبلت و لوازم جانبی با دادهٔ ترب و مدیای lonacenter."""

from __future__ import annotations

import json
import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.enums import AttributeDisplayType, ButtonDisplayStyle, ProductStatus, ProductType
from products.models import (
    Brand,
    Category,
    Inventory,
    Product,
    ProductAttribute,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
    Tag,
)
from tenants.models import Store
from tenants.services.theme_settings import ThemeSettingsService

BASE = Path(settings.BASE_DIR)
SRC_MEDIA = BASE / "_temp" / "lonacenter"
DST_MEDIA = Path(settings.MEDIA_ROOT) / "lonacenter"
CATALOG_PATH = BASE / "_temp" / "torob_catalog.json"


def media_url(*parts: str) -> str:
    return "/media/" + "/".join(parts)


def price_of(raw) -> Decimal:
    try:
        return Decimal(int(raw or 0))
    except (TypeError, ValueError):
        return Decimal(0)


class Command(BaseCommand):
    help = "پر کردن فروشگاه shop1 با برند لونا سنتر، مدیا و کالاهای ترب"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="غیرفعال کردن کالاهای قدیمی غیرمرتبط قبل از seed",
        )

    def handle(self, *args, **options):
        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("فروشگاه shop1 پیدا نشد. ابتدا seed_store را اجرا کنید."))
            return

        if not CATALOG_PATH.exists():
            self.stdout.write(self.style.ERROR(f"کاتالوگ ترب موجود نیست: {CATALOG_PATH}"))
            return

        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        if len(catalog) < 10:
            self.stdout.write(self.style.ERROR("کاتالوگ ترب کمتر از ۱۰ کالا دارد."))
            return

        self._copy_media()
        self._brand_store(store)
        cats = self._seed_categories(store)
        brands = self._seed_brands(store)
        tags = self._seed_tags(store)

        if options["reset"]:
            self._deactivate_unrelated(store)

        created = 0
        # Map catalog index → seed strategy
        plans = self._build_plans(catalog, cats, brands, tags)
        for plan in plans:
            if self._seed_product(store, plan):
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"لونا سنتر آماده است: {created} کالای جدید/به‌روز، مجموع کاتالوگ={len(catalog)}"
            )
        )

    def _copy_media(self) -> None:
        DST_MEDIA.mkdir(parents=True, exist_ok=True)
        (DST_MEDIA / "categories").mkdir(parents=True, exist_ok=True)
        (DST_MEDIA / "products").mkdir(parents=True, exist_ok=True)

        logo_src = SRC_MEDIA / "logo.PNG"
        if logo_src.exists():
            shutil.copy2(logo_src, DST_MEDIA / "logo.png")

        src_cats = SRC_MEDIA / "categories"
        if src_cats.exists():
            for f in src_cats.iterdir():
                if f.is_file():
                    shutil.copy2(f, DST_MEDIA / "categories" / f.name)

        self.stdout.write(self.style.SUCCESS(f"مدیا کپی شد → {DST_MEDIA}"))

    def _brand_store(self, store: Store) -> None:
        store.name = "لونا سنتر"
        store.status = "active"
        store.save(update_fields=["name", "status"])

        logo = media_url("lonacenter", "logo.png")
        theme = ThemeSettingsService()
        current = theme.get_theme_settings(store)
        current["logo"] = logo
        current["colors"] = {
            "primary": "#0f766e",
            "background": "#ffffff",
            "text": "#0f172a",
        }
        current["hero"] = {
            "slides": [
                {
                    "image": media_url("lonacenter", "categories", "IMG_9508.JPG"),
                    "thumbnail": media_url("lonacenter", "categories", "IMG_9508.JPG"),
                    "title": "لونا سنتر",
                    "text": "موبایل، تبلت و لوازم جانبی اصل با قیمت رقابتی",
                    "button_text": "مشاهده محصولات",
                    "button_link": "/products/mobile/",
                    "background_color": "#ecfdf5",
                },
                {
                    "image": media_url("lonacenter", "categories", "powerbank.jpg"),
                    "thumbnail": media_url("lonacenter", "categories", "powerbank.jpg"),
                    "title": "پاوربانک و شارژ",
                    "text": "انکر، باسئوس و برندهای معتبر",
                    "button_text": "پاوربانک‌ها",
                    "button_link": "/products/powerbank/",
                    "background_color": "#f0fdfa",
                },
                {
                    "image": media_url("lonacenter", "categories", "handsfree.jpg"),
                    "thumbnail": media_url("lonacenter", "categories", "handsfree.jpg"),
                    "title": "هندزفری و ایربادز",
                    "text": "گلکسی بادز، ردمی بادز و بیشتر",
                    "button_text": "هندزفری‌ها",
                    "button_link": "/products/handsfree/",
                    "background_color": "#f8fafc",
                },
            ]
        }
        theme.update_theme_settings(store, current)
        self.stdout.write(self.style.SUCCESS("برندینگ فروشگاه و لوگو تنظیم شد."))

    def _seed_categories(self, store: Store) -> dict[str, Category]:
        specs = [
            ("mobile", "موبایل", "IMG_9508.JPG", 1),
            ("tablet", "تبلت", "bfeb7c.jpg", 2),
            ("handsfree", "هندزفری و ایربادز", "handsfree.jpg", 3),
            ("powerbank", "پاوربانک", "powerbank.jpg", 4),
            ("charger", "شارژر و کابل", "cdb29c80769b0967d550fb7c3b9e3d41bcc5c668_1678009665.jpg", 5),
            ("cases", "قاب و گلس", "8948c22b78a85ec54c944d842da991804b942927_1632295762.jpg", 6),
            ("parts", "قطعات موبایل", "mobile-parts.jpg", 7),
        ]
        out: dict[str, Category] = {}
        for slug, name, img, order in specs:
            image = media_url("lonacenter", "categories", img)
            cat, created = Category.objects.update_or_create(
                store=store,
                slug=slug,
                defaults={
                    "name": name,
                    "image": image,
                    "sort_order": order,
                    "is_active": True,
                    "description": f"دسته‌بندی {name} — لونا سنتر",
                },
            )
            out[slug] = cat
            self.stdout.write(("+" if created else "~") + f" category {slug}")

        # Hide legacy demo categories and empty placeholder categories
        Category.objects.filter(
            store=store, slug__in=["electronics", "fashion", "phones", "parts"]
        ).update(is_active=False)
        return out

    def _seed_brands(self, store: Store) -> dict[str, Brand]:
        names = {
            "samsung": "سامسونگ",
            "xiaomi": "شیائومی",
            "apple": "اپل",
            "anker": "انکر",
            "baseus": "باسئوس",
            "mcdodo": "مک دودو",
            "other": "متفرقه",
        }
        out = {}
        for slug, name in names.items():
            brand, _ = Brand.objects.get_or_create(
                store=store, slug=slug, defaults={"name": name, "is_active": True}
            )
            if brand.name != name:
                brand.name = name
                brand.is_active = True
                brand.save(update_fields=["name", "is_active"])
            out[slug] = brand
        return out

    def _seed_tags(self, store: Store) -> dict[str, Tag]:
        out = {}
        for slug, name in [("new", "جدید"), ("featured", "ویژه"), ("torob", "ترب")]:
            tag, _ = Tag.objects.get_or_create(store=store, slug=slug, defaults={"name": name})
            out[slug] = tag
        return out

    def _deactivate_unrelated(self, store: Store) -> None:
        qs = Product.objects.filter(store=store).exclude(slug__startswith="lc-")
        n = qs.update(status=ProductStatus.DRAFT)
        self.stdout.write(self.style.WARNING(f"{n} کالای قدیمی به draft رفت (غیر lc-)."))

    def _build_plans(self, catalog, cats, brands, tags) -> list[dict]:
        """Attach category/brand/variant strategy to each Torob row."""

        def pick(idx: int) -> dict:
            return catalog[idx]

        plans = [
            {
                "slug": "lc-samsung-s26-ultra",
                "item": pick(0),
                "category": cats["mobile"],
                "brand": brands["samsung"],
                "featured": True,
                "variant": "phone_storage_color",
                "storages": [("1TB", 0), ("512GB", -25000000)],
                "colors": [("مشکی", "#111111", "black"), ("خاکستری", "#6b7280", "gray")],
            },
            {
                "slug": "lc-samsung-s24-ultra",
                "item": pick(1),
                "category": cats["mobile"],
                "brand": brands["samsung"],
                "featured": True,
                "variant": "phone_storage_color",
                "storages": [("256GB", 0), ("512GB", 12000000)],
                "colors": [
                    ("مشکی تیتانیوم", "#1f2937", "black"),
                    ("خاکستری تیتانیوم", "#9ca3af", "gray"),
                    ("بنفش تیتانیوم", "#7c3aed", "violet"),
                ],
            },
            {
                "slug": "lc-redmi-note-14-5g",
                "item": pick(2),
                "category": cats["mobile"],
                "brand": brands["xiaomi"],
                "featured": True,
                "variant": "phone_storage_color",
                "storages": [("256GB", 0), ("128GB", -4000000)],
                "colors": [("مشکی", "#111111", "black"), ("آبی", "#2563eb", "blue"), ("سبز", "#16a34a", "green")],
            },
            {
                "slug": "lc-redmi-note-13-pro",
                "item": pick(3),
                "category": cats["mobile"],
                "brand": brands["xiaomi"],
                "featured": False,
                "variant": "simple",
            },
            {
                "slug": "lc-iphone-16-promax",
                "item": pick(4),
                "category": cats["mobile"],
                "brand": brands["apple"],
                "featured": True,
                "variant": "phone_storage_color",
                "storages": [("256GB", 0), ("512GB", 18000000)],
                "colors": [("مشکی", "#111111,#2a2a2a", "black"), ("طبیعی", "#d6d3d1,#a8a29e", "natural"), ("سفید", "#f8fafc,#e2e8f0", "white")],
            },
            {
                "slug": "lc-iphone-13",
                "item": pick(5),
                "category": cats["mobile"],
                "brand": brands["apple"],
                "featured": False,
                "variant": "phone_storage_color",
                "storages": [("128GB", 0), ("256GB", 7000000)],
                "colors": [("میدنایت", "#111827,#1e293b", "midnight"), ("آبی", "#3b82f6,#1d4ed8", "blue"), ("صورتی", "#fb7185,#f472b6", "pink")],
            },
            {
                "slug": "lc-tab-a9",
                "item": pick(6),
                "category": cats["tablet"],
                "brand": brands["samsung"],
                "featured": True,
                "variant": "simple",
            },
            {
                "slug": "lc-tab-s10-fe-plus",
                "item": pick(7),
                "category": cats["tablet"],
                "brand": brands["samsung"],
                "featured": False,
                "variant": "simple",
            },
            {
                "slug": "lc-anker-a1384",
                "item": pick(8),
                "category": cats["powerbank"],
                "brand": brands["anker"],
                "featured": True,
                "variant": "color_only",
                "colors": [("مشکی", "#111111", "black"), ("سفید", "#f8fafc", "white")],
            },
            {
                "slug": "lc-anker-a1257",
                "item": pick(9),
                "category": cats["powerbank"],
                "brand": brands["anker"],
                "featured": False,
                "deal": True,
                "variant": "simple",
            },
            {
                "slug": "lc-powerbank-levano",
                "item": pick(10),
                "category": cats["powerbank"],
                "brand": brands["other"],
                "featured": False,
                "variant": "simple",
            },
            {
                "slug": "lc-baseus-bipow",
                "item": pick(11),
                "category": cats["powerbank"],
                "brand": brands["baseus"],
                "featured": True,
                "variant": "color_only",
                "colors": [("مشکی", "#111111", "black"), ("سفید", "#ffffff", "white")],
            },
            {
                "slug": "lc-buds3-cover",
                "item": pick(12),
                "category": cats["cases"],
                "brand": brands["samsung"],
                "featured": False,
                "variant": "simple",
            },
            {
                "slug": "lc-galaxy-buds-3-pro",
                "item": pick(13),
                "category": cats["handsfree"],
                "brand": brands["samsung"],
                "featured": True,
                "variant": "color_only",
                "colors": [("نقره‌ای", "#c0c0c0", "silver"), ("مشکی", "#111111", "black")],
            },
            {
                "slug": "lc-redmi-buds-5-pro",
                "item": pick(14),
                "category": cats["handsfree"],
                "brand": brands["xiaomi"],
                "featured": True,
                "variant": "color_only",
                "colors": [("مشکی", "#111111", "black"), ("سفید", "#f8fafc", "white")],
            },
            {
                "slug": "lc-samsung-25w-charger",
                "item": pick(15),
                "category": cats["charger"],
                "brand": brands["samsung"],
                "featured": False,
                "deal": True,
                "variant": "simple",
            },
            {
                "slug": "lc-mcdodo-typec-cable",
                "item": pick(16),
                "category": cats["charger"],
                "brand": brands["mcdodo"],
                "featured": False,
                "variant": "color_only",
                "colors": [("مشکی", "#111111", "black"), ("قرمز", "#dc2626", "red")],
            },
            {
                "slug": "lc-privacy-glass-s23u",
                "item": pick(17),
                "category": cats["cases"],
                "brand": brands["samsung"],
                "featured": False,
                "variant": "simple",
            },
            {
                "slug": "lc-silicone-case-s24u",
                "item": pick(18),
                "category": cats["cases"],
                "brand": brands["samsung"],
                "featured": True,
                "variant": "color_only",
                "colors": [
                    ("مشکی", "#111111", "black"),
                    ("شفاف", "#e5e7eb", "clear"),
                    ("صورتی", "#f9a8d4", "pink"),
                    ("آبی", "#60a5fa", "blue"),
                ],
            },
        ]
        for p in plans:
            p["tags"] = tags
        return plans

    def _seed_product(self, store: Store, plan: dict) -> bool:
        item = plan["item"]
        slug = plan["slug"]
        name = (item.get("name") or "").strip()
        if not name:
            return False

        price = price_of(item.get("price"))
        if price <= 0:
            price = Decimal(1000000)

        image = (item.get("image") or "").strip()
        short = "موجود در لونا سنتر — قیمت به‌روز و ارسال سریع"
        description = (
            f"{name}\n\n"
            f"خرید از لونا سنتر، فروشگاه موبایل و لوازم جانبی.\n"
            f"برای مقایسه قیمت بازار می‌توانید محصول را در ترب هم جستجو کنید."
        )

        # Keep compare_price only when we intentionally want a visible deal (≥8%).
        compare = None
        if plan.get("featured") and price > 0:
            compare = (price * Decimal("1.12")).quantize(Decimal("1"))
        elif plan.get("deal") and price > 0:
            compare = (price * Decimal("1.18")).quantize(Decimal("1"))

        product, created = Product.objects.update_or_create(
            store=store,
            slug=slug,
            defaults={
                "name": name[:300],
                "short_description": short[:500],
                "description": description,
                "category": plan["category"],
                "brand": plan["brand"],
                "product_type": (
                    ProductType.VARIABLE if plan["variant"] != "simple" else ProductType.SIMPLE
                ),
                "status": ProductStatus.ACTIVE,
                "base_price": price,
                "compare_price": compare,
                "sku": slug.upper().replace("-", "")[:40],
                "is_featured": bool(plan.get("featured")),
                "meta_title": name[:70],
                "meta_description": short[:160],
            },
        )

        tags = plan["tags"]
        product.tags.set([tags["torob"], tags["new"]] + ([tags["featured"]] if plan.get("featured") else []))

        if image:
            ProductImage.objects.filter(product=product).delete()
            ProductImage.objects.create(
                product=product,
                image=image,
                alt_text=name[:200],
                is_primary=True,
                sort_order=0,
            )

        # Clear old variants/inventory for re-seed consistency
        Inventory.objects.filter(product=product).delete()
        product.variants.all().delete()

        kind = plan["variant"]
        if kind == "simple":
            Inventory.objects.create(product=product, quantity=15)
        elif kind == "color_only":
            self._seed_color_variants(store, product, price, plan.get("colors") or [])
        elif kind == "phone_storage_color":
            self._seed_phone_variants(
                store,
                product,
                price,
                plan.get("storages") or [],
                plan.get("colors") or [],
            )

        mark = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"{mark}: {slug}"))
        return True

    def _attr(self, store, slug, name, display_type, sort_order=0, button_style=""):
        defaults = {
            "name": name,
            "display_type": display_type,
            "sort_order": sort_order,
        }
        if button_style:
            defaults["button_style"] = button_style
        attr, _ = ProductAttribute.objects.get_or_create(store=store, slug=slug, defaults=defaults)
        return attr

    def _attr_value(self, attr, slug, value, sort_order=0, color_code=""):
        from products.utils import normalize_color_code

        color_code = normalize_color_code(color_code)
        val, _ = ProductAttributeValue.objects.get_or_create(
            attribute=attr,
            slug=slug,
            defaults={"value": value, "sort_order": sort_order, "color_code": color_code},
        )
        if color_code and val.color_code != color_code:
            val.color_code = color_code
            val.value = value
            val.save(update_fields=["color_code", "value"])
        return val

    def _seed_color_variants(self, store, product, base_price: Decimal, colors: list) -> None:
        color_attr = self._attr(
            store, "color", "رنگ", AttributeDisplayType.COLOR, sort_order=0
        )
        for idx, (label, code, av_slug) in enumerate(colors):
            val = self._attr_value(color_attr, av_slug, label, sort_order=idx, color_code=code)
            delta = Decimal(idx * 50000)
            variant = ProductVariant.objects.create(
                product=product,
                sku=f"{product.sku}-{av_slug.upper()}"[:40],
                price=base_price + delta,
                compare_price=base_price + delta + Decimal(200000),
                is_active=True,
            )
            variant.attributes.set([val])
            Inventory.objects.create(product=product, variant=variant, quantity=8 + idx)

    def _seed_phone_variants(self, store, product, base_price, storages, colors) -> None:
        color_attr = self._attr(
            store, "color", "رنگ", AttributeDisplayType.COLOR, sort_order=0
        )
        storage_attr = self._attr(
            store,
            "lc-phone-storage",
            "حافظه",
            AttributeDisplayType.BUTTON,
            sort_order=1,
            button_style=ButtonDisplayStyle.TEXT,
        )

        color_vals = []
        for idx, (label, code, av_slug) in enumerate(colors):
            color_vals.append(
                self._attr_value(color_attr, av_slug, label, sort_order=idx, color_code=code)
            )

        storage_vals = []
        for idx, (label, delta) in enumerate(storages):
            av_slug = slugify(label) or f"st-{idx}"
            storage_vals.append(
                (self._attr_value(storage_attr, av_slug, label, sort_order=idx), Decimal(delta))
            )

        # Limit combinatorial explosion: all colors × storages (max ~6–9)
        for c_idx, cval in enumerate(color_vals):
            for s_idx, (sval, delta) in enumerate(storage_vals):
                price = base_price + delta + Decimal(c_idx * 150000)
                if price < Decimal(100000):
                    price = base_price
                sku = f"{product.sku}-{cval.slug[:6]}-{sval.slug[:8]}".upper()[:40]
                variant = ProductVariant.objects.create(
                    product=product,
                    sku=sku,
                    price=price,
                    compare_price=price + Decimal(1500000),
                    is_active=True,
                )
                variant.attributes.set([cval, sval])
                Inventory.objects.create(
                    product=product,
                    variant=variant,
                    quantity=max(2, 10 - c_idx - s_idx),
                )
