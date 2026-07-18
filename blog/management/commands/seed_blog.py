"""Seed blog plugin and sample posts."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from blog.models import BlogCategory, BlogPost, BlogTag
from tenants.models import Plugin, Store, StorePlugin


class Command(BaseCommand):
    help = "Seed blog plugin and sample posts"

    def handle(self, *args, **options):
        plugin, _ = Plugin.objects.get_or_create(
            codename="blog",
            defaults={"name": "Blog", "description": "Blog and articles", "is_active": True},
        )

        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("Run seed_store first."))
            return

        StorePlugin.objects.update_or_create(store=store, plugin=plugin, defaults={"is_enabled": True})

        category, _ = BlogCategory.objects.get_or_create(
            store=store,
            slug="news",
            defaults={"name": "اخبار", "description": "اخبار فروشگاه", "is_active": True},
        )
        tag, _ = BlogTag.objects.get_or_create(store=store, slug="shop", defaults={"name": "فروشگاه"})
        author = User.objects.filter(is_superuser=True).first()

        post, created = BlogPost.objects.get_or_create(
            store=store,
            slug="welcome",
            defaults={
                "title": "به فروشگاه ما خوش آمدید",
                "excerpt": "اولین مطلب وبلاگ",
                "content": "<p>این یک مطلب نمونه برای فاز وبلاگ است.</p>",
                "category": category,
                "author": author,
                "featured_image": "",
                "is_published": True,
                "published_at": timezone.now(),
                "meta_title": "خوش آمدید",
                "meta_description": "اولین مطلب وبلاگ فروشگاه",
            },
        )
        if created:
            post.tags.add(tag)
            self.stdout.write(self.style.SUCCESS(f"Created blog post: {post.slug}"))

        self.stdout.write(self.style.SUCCESS("Blog seeded successfully."))
