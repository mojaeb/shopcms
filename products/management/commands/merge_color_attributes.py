"""Merge duplicate «رنگ» attributes into a single store-level color attribute."""

from django.core.management.base import BaseCommand
from django.db import transaction

from products.enums import AttributeDisplayType
from products.models import ProductAttribute, ProductAttributeValue, ProductVariant
from products.utils import normalize_color_code
from tenants.models import Store


class Command(BaseCommand):
    help = "ادغام همه ویژگی‌های «رنگ» فروشگاه در یک ویژگی واحد (slug=color)"

    def add_arguments(self, parser):
        parser.add_argument("--store", default="shop1", help="Store slug")
        parser.add_argument(
            "--keep-slug",
            default="color",
            help="Canonical attribute slug (default: color)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        store = Store.objects.filter(slug=options["store"]).first()
        if not store:
            self.stdout.write(self.style.WARNING(f"Store {options['store']} not found."))
            return

        keep_slug = options["keep_slug"]
        canonical, created = ProductAttribute.objects.get_or_create(
            store=store,
            slug=keep_slug,
            defaults={
                "name": "رنگ",
                "display_type": AttributeDisplayType.COLOR,
                "sort_order": 0,
            },
        )
        if not created:
            canonical.name = "رنگ"
            canonical.display_type = AttributeDisplayType.COLOR
            if canonical.sort_order != 0:
                canonical.sort_order = 0
            canonical.save(update_fields=["name", "display_type", "sort_order"])

        # All named رنگ, plus any other display_type=color (except junk we delete)
        duplicates = (
            ProductAttribute.objects.filter(store=store)
            .filter(name="رنگ")
            .exclude(pk=canonical.pk)
        )
        extras = ProductAttribute.objects.filter(
            store=store,
            display_type=AttributeDisplayType.COLOR,
        ).exclude(pk=canonical.pk).exclude(name="رنگ")

        remapped = 0
        for old in list(duplicates):
            remapped += self._merge_attr(canonical, old)
            self.stdout.write(f"merged attribute #{old.id} ({old.slug}) → {keep_slug}")
            old.delete()

        for junk in list(extras):
            used = ProductVariant.objects.filter(attributes__attribute=junk).exists()
            if used:
                remapped += self._merge_attr(canonical, junk)
                self.stdout.write(f"merged extra color attr #{junk.id} ({junk.name}/{junk.slug})")
            else:
                self.stdout.write(f"deleted unused color attr #{junk.id} ({junk.name}/{junk.slug})")
            junk.delete()

        value_count = canonical.values.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Canonical رنگ id={canonical.id} slug={keep_slug} "
                f"values={value_count} remapped_links={remapped}"
            )
        )

    def _merge_attr(self, canonical: ProductAttribute, old: ProductAttribute) -> int:
        remapped = 0
        for old_val in old.values.all():
            color = normalize_color_code(old_val.color_code)
            new_val, created = ProductAttributeValue.objects.get_or_create(
                attribute=canonical,
                slug=old_val.slug,
                defaults={
                    "value": old_val.value,
                    "color_code": color,
                    "icon": old_val.icon,
                    "sort_order": old_val.sort_order,
                },
            )
            if not created:
                changed = False
                if color and not new_val.color_code:
                    new_val.color_code = color
                    changed = True
                # Prefer longer/more descriptive label
                if len(old_val.value) > len(new_val.value):
                    new_val.value = old_val.value
                    changed = True
                if changed:
                    new_val.save()

            through = ProductVariant.attributes.through
            links = list(
                through.objects.filter(productattributevalue_id=old_val.id).values_list(
                    "productvariant_id", flat=True
                )
            )
            for variant_id in links:
                through.objects.get_or_create(
                    productvariant_id=variant_id,
                    productattributevalue_id=new_val.id,
                )
                through.objects.filter(
                    productvariant_id=variant_id,
                    productattributevalue_id=old_val.id,
                ).delete()
                remapped += 1
        return remapped
