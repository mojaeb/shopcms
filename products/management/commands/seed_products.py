"""Seed sample products."""

from itertools import product as cartesian

from django.core.management.base import BaseCommand

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

ICON = "https://api.iconify.design/lucide/{name}.svg?color=%23111"


class Command(BaseCommand):
    help = "Seed sample products for development"

    def handle(self, *args, **options):
        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("Run seed_store first."))
            return

        electronics, _ = Category.objects.get_or_create(
            store=store, slug="electronics",
            defaults={"name": "لوازم الکترونیکی", "is_active": True},
        )
        phones, _ = Category.objects.get_or_create(
            store=store, slug="phones", parent=electronics,
            defaults={"name": "موبایل", "is_active": True},
        )
        fashion, _ = Category.objects.get_or_create(
            store=store, slug="fashion",
            defaults={"name": "مد و پوشاک", "is_active": True},
        )
        brand, _ = Brand.objects.get_or_create(
            store=store, slug="samsung",
            defaults={"name": "سامسونگ", "is_active": True},
        )
        sport_brand, _ = Brand.objects.get_or_create(
            store=store, slug="modern-fit",
            defaults={"name": "مدرن‌فیت", "is_active": True},
        )
        tag, _ = Tag.objects.get_or_create(store=store, slug="new", defaults={"name": "جدید"})
        featured_tag, _ = Tag.objects.get_or_create(store=store, slug="featured", defaults={"name": "ویژه"})

        product, created = Product.objects.get_or_create(
            store=store,
            slug="galaxy-s24",
            defaults={
                "name": "گلکسی S24",
                "short_description": "گوشی هوشمند سامسونگ",
                "description": "محصول نمونه برای تست فاز ۷",
                "category": phones,
                "brand": brand,
                "product_type": ProductType.SIMPLE,
                "status": ProductStatus.ACTIVE,
                "base_price": 45000000,
                "compare_price": 48000000,
                "sku": "SAM-S24",
                "is_featured": True,
                "meta_title": "گلکسی S24",
                "meta_description": "خرید گلکسی S24",
            },
        )
        if created:
            product.tags.add(tag)
            ProductImage.objects.create(
                product=product,
                image="https://placehold.co/600x600/1a1a2e/white?text=Galaxy+S24",
                is_primary=True,
            )
            Inventory.objects.create(product=product, quantity=10)
            self.stdout.write(self.style.SUCCESS(f"Created product: {product.slug}"))

        product2, created = Product.objects.get_or_create(
            store=store,
            slug="sample-tshirt",
            defaults={
                "name": "تیشرت نمونه",
                "category": electronics,
                "product_type": ProductType.SIMPLE,
                "status": ProductStatus.ACTIVE,
                "base_price": 350000,
                "sku": "TSH-001",
            },
        )
        if created:
            ProductImage.objects.create(
                product=product2,
                image="https://placehold.co/400x400/e94560/white?text=T-Shirt",
                is_primary=True,
            )
            Inventory.objects.create(product=product2, quantity=50)

        self._seed_variable_hoodie(store, fashion, sport_brand, featured_tag)
        self._seed_mobile_phone(store, phones, brand, tag)
        self.stdout.write(self.style.SUCCESS("Products seeded successfully."))

    def _seed_variable_hoodie(self, store, category, brand, tag):
        """Multi-variant demo product showcasing Color, List, and Button display types."""
        slug = "premium-hoodie"
        if Product.objects.filter(store=store, slug=slug).exists():
            self.stdout.write(f"Variable product already exists: {slug}")
            return

        color_attr, _ = ProductAttribute.objects.get_or_create(
            store=store,
            slug="hoodie-color",
            defaults={
                "name": "رنگ",
                "display_type": AttributeDisplayType.COLOR,
                "sort_order": 0,
            },
        )
        color_values = {}
        for idx, (label, code, av_slug) in enumerate([
            ("مشکی", "#111111", "black"),
            ("سفید", "#f5f5f5", "white"),
            ("سرمه‌ای", "#1e3a5f", "navy"),
        ]):
            val, _ = ProductAttributeValue.objects.get_or_create(
                attribute=color_attr,
                slug=av_slug,
                defaults={"value": label, "color_code": code, "sort_order": idx},
            )
            color_values[av_slug] = val

        size_attr, _ = ProductAttribute.objects.get_or_create(
            store=store,
            slug="hoodie-size",
            defaults={
                "name": "سایز",
                "display_type": AttributeDisplayType.LIST,
                "sort_order": 1,
            },
        )
        size_values = {}
        for idx, (label, av_slug) in enumerate([("S", "s"), ("M", "m"), ("L", "l")]):
            val, _ = ProductAttributeValue.objects.get_or_create(
                attribute=size_attr,
                slug=av_slug,
                defaults={"value": label, "sort_order": idx},
            )
            size_values[av_slug] = val

        badge_attr, _ = ProductAttribute.objects.get_or_create(
            store=store,
            slug="hoodie-badge",
            defaults={
                "name": "نشان",
                "display_type": AttributeDisplayType.BUTTON,
                "button_style": ButtonDisplayStyle.ICON,
                "sort_order": 2,
            },
        )
        badge_values = {}
        for idx, (label, av_slug, icon_name) in enumerate([
            ("ستاره", "star", "star"),
            ("قلب", "heart", "heart"),
        ]):
            val, _ = ProductAttributeValue.objects.get_or_create(
                attribute=badge_attr,
                slug=av_slug,
                defaults={"value": label, "icon": ICON.format(name=icon_name), "sort_order": idx},
            )
            badge_values[av_slug] = val

        fit_attr, _ = ProductAttribute.objects.get_or_create(
            store=store,
            slug="hoodie-fit",
            defaults={
                "name": "فرم دوخت",
                "display_type": AttributeDisplayType.BUTTON,
                "button_style": ButtonDisplayStyle.TEXT,
                "sort_order": 3,
            },
        )
        fit_values = {}
        for idx, (label, av_slug) in enumerate([("اسلیم", "slim"), ("استاندارد", "regular")]):
            val, _ = ProductAttributeValue.objects.get_or_create(
                attribute=fit_attr,
                slug=av_slug,
                defaults={"value": label, "sort_order": idx},
            )
            fit_values[av_slug] = val

        ship_attr, _ = ProductAttribute.objects.get_or_create(
            store=store,
            slug="hoodie-shipping",
            defaults={
                "name": "بسته‌بندی",
                "display_type": AttributeDisplayType.BUTTON,
                "button_style": ButtonDisplayStyle.ICON_TEXT,
                "sort_order": 4,
            },
        )
        ship_values = {}
        for idx, (label, av_slug, icon_name) in enumerate([
            ("هدیه‌ای", "gift", "gift"),
            ("استاندارد", "standard", "package"),
        ]):
            val, _ = ProductAttributeValue.objects.get_or_create(
                attribute=ship_attr,
                slug=av_slug,
                defaults={"value": label, "icon": ICON.format(name=icon_name), "sort_order": idx},
            )
            ship_values[av_slug] = val

        hoodie = Product.objects.create(
            store=store,
            slug=slug,
            name="هودی پریمیوم",
            short_description="هودی چند-variant با انواع نمایش Color، List و Button",
            description=(
                "محصول نمونه برای تست variantهای چندگانه.\n"
                "رنگ به‌صورت swatch، سایز به‌صورت لیست، نشان فقط آیکون، "
                "فرم دوخت فقط متن، و بسته‌بندی آیکون + متن نمایش داده می‌شود."
            ),
            category=category,
            brand=brand,
            product_type=ProductType.VARIABLE,
            status=ProductStatus.ACTIVE,
            base_price=890000,
            compare_price=990000,
            sku="HD-PREM",
            is_featured=True,
            meta_title="هودی پریمیوم",
            meta_description="خرید هودی پریمیوم با variantهای متنوع",
        )
        hoodie.tags.add(tag)

        ProductImage.objects.bulk_create([
            ProductImage(
                product=hoodie,
                image="https://placehold.co/800x800/111/white?text=Premium+Hoodie",
                alt_text="هودی پریمیوم",
                is_primary=True,
                sort_order=0,
            ),
            ProductImage(
                product=hoodie,
                image="https://placehold.co/800x800/1e3a5f/white?text=Detail",
                alt_text="جزئیات هودی",
                sort_order=1,
            ),
            ProductImage(
                product=hoodie,
                image="https://placehold.co/800x800/f5f5f5/111?text=Back",
                alt_text="پشت هودی",
                sort_order=2,
            ),
        ])

        color_slugs = ["black", "white", "navy"]
        size_slugs = ["s", "m", "l"]
        badge_slugs = ["star", "heart"]
        fit_slugs = ["slim", "regular"]
        ship_slugs = ["gift", "standard"]

        variant_count = 0
        for c_slug, s_slug, b_slug, f_slug, sh_slug in cartesian(
            color_slugs, size_slugs, badge_slugs, fit_slugs, ship_slugs
        ):
            variant_count += 1
            price = 890000
            if c_slug == "navy":
                price += 30000
            if s_slug == "l":
                price += 20000
            if sh_slug == "gift":
                price += 50000

            sku = f"HD-{c_slug[:3].upper()}-{s_slug.upper()}-{b_slug[:2].upper()}-{f_slug[:2].upper()}-{sh_slug[:3].upper()}"
            variant = ProductVariant.objects.create(
                product=hoodie,
                sku=sku,
                price=price,
                compare_price=price + 100000 if sh_slug == "gift" else None,
                is_active=True,
            )
            variant.attributes.set([
                color_values[c_slug],
                size_values[s_slug],
                badge_values[b_slug],
                fit_values[f_slug],
                ship_values[sh_slug],
            ])
            stock = 8 if c_slug != "white" else 3
            if s_slug == "l":
                stock = max(1, stock - 2)
            Inventory.objects.create(variant=variant, product=hoodie, quantity=stock)

        self.stdout.write(self.style.SUCCESS(
            f"Created variable product: {slug} with {variant_count} variants"
        ))

    def _seed_mobile_phone(self, store, category, brand, tag):
        """Sparse variants: color → RAM branches; warranty only on blue + RAM 2."""
        slug = "smart-mobile-x"
        if Product.objects.filter(store=store, slug=slug).exists():
            self.stdout.write(f"Mobile product already exists: {slug}")
            return

        color_attr, _ = ProductAttribute.objects.get_or_create(
            store=store,
            slug="mobile-color",
            defaults={
                "name": "رنگ",
                "display_type": AttributeDisplayType.COLOR,
                "sort_order": 0,
            },
        )
        colors = {}
        for idx, (label, code, av_slug) in enumerate([
            ("سبز", "#22c55e", "green"),
            ("آبی", "#3b82f6", "blue"),
        ]):
            val, _ = ProductAttributeValue.objects.get_or_create(
                attribute=color_attr,
                slug=av_slug,
                defaults={"value": label, "color_code": code, "sort_order": idx},
            )
            colors[av_slug] = val

        ram_attr, _ = ProductAttribute.objects.get_or_create(
            store=store,
            slug="mobile-ram",
            defaults={
                "name": "رم",
                "display_type": AttributeDisplayType.LIST,
                "sort_order": 1,
            },
        )
        rams = {}
        for idx, (label, av_slug) in enumerate([
            ("رم ۱", "ram-1"),
            ("رم ۲", "ram-2"),
            ("رم ۴", "ram-4"),
        ]):
            val, _ = ProductAttributeValue.objects.get_or_create(
                attribute=ram_attr,
                slug=av_slug,
                defaults={"value": label, "sort_order": idx},
            )
            rams[av_slug] = val

        warranty_attr, _ = ProductAttribute.objects.get_or_create(
            store=store,
            slug="mobile-warranty",
            defaults={
                "name": "گارانتی",
                "display_type": AttributeDisplayType.BUTTON,
                "button_style": ButtonDisplayStyle.TEXT,
                "sort_order": 2,
            },
        )
        warranties = {}
        for idx, (label, av_slug) in enumerate([
            ("با گارانتی", "with-warranty"),
            ("بدون گارانتی", "no-warranty"),
        ]):
            val, _ = ProductAttributeValue.objects.get_or_create(
                attribute=warranty_attr,
                slug=av_slug,
                defaults={"value": label, "sort_order": idx},
            )
            warranties[av_slug] = val

        mobile = Product.objects.create(
            store=store,
            slug=slug,
            name="موبایل Smart X",
            short_description="موبایل با variantهای وابسته — رنگ، رم و گارانتی شرطی",
            description=(
                "مثال variantهای sparse:\n"
                "• سبز: رم ۲ یا رم ۴\n"
                "• آبی: رم ۱ یا رم ۲\n"
                "• فقط «آبی + رم ۲» گزینه گارانتی دارد\n"
                "• سایر ترکیب‌ها گارانتی ندارند"
            ),
            category=category,
            brand=brand,
            product_type=ProductType.VARIABLE,
            status=ProductStatus.ACTIVE,
            base_price=14000000,
            compare_price=15500000,
            sku="MOB-SMX",
            is_featured=True,
            meta_title="موبایل Smart X",
            meta_description="خرید موبایل Smart X با انتخاب رنگ و رم",
        )
        mobile.tags.add(tag)

        ProductImage.objects.bulk_create([
            ProductImage(
                product=mobile,
                image="https://placehold.co/800x800/22c55e/white?text=Smart+X+Green",
                alt_text="موبایل سبز",
                is_primary=True,
                sort_order=0,
            ),
            ProductImage(
                product=mobile,
                image="https://placehold.co/800x800/3b82f6/white?text=Smart+X+Blue",
                alt_text="موبایل آبی",
                sort_order=1,
            ),
        ])

        sparse_variants = [
            ("MOB-G-R2", 15000000, 5, [colors["green"], rams["ram-2"]]),
            ("MOB-G-R4", 17000000, 3, [colors["green"], rams["ram-4"]]),
            ("MOB-B-R1", 14000000, 4, [colors["blue"], rams["ram-1"]]),
            ("MOB-B-R2-W", 16500000, 2, [colors["blue"], rams["ram-2"], warranties["with-warranty"]]),
            ("MOB-B-R2-NW", 16000000, 6, [colors["blue"], rams["ram-2"], warranties["no-warranty"]]),
        ]

        for sku, price, stock, attr_values in sparse_variants:
            variant = ProductVariant.objects.create(
                product=mobile,
                sku=sku,
                price=price,
                compare_price=price + 500000,
                is_active=True,
            )
            variant.attributes.set(attr_values)
            Inventory.objects.create(variant=variant, product=mobile, quantity=stock)

        self.stdout.write(self.style.SUCCESS(
            f"Created sparse mobile product: {slug} with {len(sparse_variants)} variants"
        ))

