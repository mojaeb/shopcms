"""Seed Lona Center blog categories and articles."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from blog.models import BlogCategory, BlogPost, BlogTag
from tenants.models import Plugin, Store, StorePlugin

POSTS = [
    {
        "slug": "guide-buy-phone-2026",
        "title": "راهنمای خرید گوشی در ۱۴۰۵؛ چه چیزی واقعاً مهم است؟",
        "excerpt": "قبل از خرید پرچمدار یا میان‌رده، این معیارها را چک کنید تا پولتان هدر نرود.",
        "category": "guides",
        "tags": ["موبایل", "راهنمای خرید"],
        "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=1200&q=80",
        "days_ago": 1,
        "content": """
<p>خرید گوشی فقط مقایسه مگاپیکسل و رم نیست. در لونا سنتر معمولاً به مشتریان می‌گوییم روی این چهار مورد تمرکز کنند:</p>
<ul>
<li><strong>نیاز واقعی:</strong> بازی سنگین، عکاسی، یا فقط تماس و پیام؟</li>
<li><strong>پشتیبانی نرم‌افزاری:</strong> آپدیت امنیتی طولانی‌مدت ارزش خرید را بالا می‌برد.</li>
<li><strong>باتری و شارژ:</strong> ظرفیت به‌علاوه سرعت شارژ، نه فقط عدد میلی‌آمپر.</li>
<li><strong>گارانتی معتبر:</strong> مخصوصاً برای گوشی‌های وارداتی.</li>
</ul>
<p>اگر بین دو مدل مردد هستید، در صفحه <a href="/category/mobile/">موبایل</a> مشخصات و قیمت‌ها را کنار هم ببینید یا از پشتیبانی لونا سنتر مشاوره بگیرید.</p>
""",
    },
    {
        "slug": "powerbank-tips",
        "title": "پاوربانک مناسب سفر؛ ظرفیت، وات و ایمنی",
        "excerpt": "برای سفر و دانشگاه چه ظرفیتی بخرید و چرا وات خروجی مهم‌تر از ظاهر است.",
        "category": "guides",
        "tags": ["پاوربانک", "لوازم جانبی"],
        "image": "https://images.unsplash.com/photo-1556656793-08538906a9f8?auto=format&fit=crop&w=1200&q=80",
        "days_ago": 3,
        "content": """
<p>یک پاوربانک ضعیف بیشتر از اینکه نجات‌تان دهد، اعصاب‌تان را خرد می‌کند. پیشنهاد ما:</p>
<ol>
<li>برای یک‌روز بیرون از خانه: حدود ۱۰٬۰۰۰ میلی‌آمپر</li>
<li>برای سفر دو-سه‌روزه: ۲۰٬۰۰۰ میلی‌آمپر با خروجی ۱۸ وات به بالا</li>
<li>حتماً برند معتبر با محافظت در برابر جریان اضافه انتخاب کنید</li>
</ol>
<p>در دسته <a href="/category/powerbank/">پاوربانک</a> مدل‌های انکر و باسئوس را با ظرفیت و توان مشخص می‌بینید.</p>
""",
    },
    {
        "slug": "earbuds-vs-wired",
        "title": "ایربادز بی‌سیم یا هندزفری سیمی؟ مقایسه کاربردی",
        "excerpt": "کدام گزینه برای تماس، ورزش و استفاده روزمره بهتر است.",
        "category": "reviews",
        "tags": ["هندزفری", "ایربادز"],
        "image": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=1200&q=80",
        "days_ago": 5,
        "content": """
<p>ایربادز بی‌سیم آزادی حرکت می‌دهد، اما سیمی هنوز در دو سناریو برنده است: تماس طولانی و محیط‌های خیلی شلوغ با نویز زیاد.</p>
<p>اگر بیشتر ورزش یا رفت‌وآمد می‌کنید، مدل‌های Buds با کیس شارژ انتخاب بهتری‌اند. اگر روی کیفیت مکالمه حساسید، قبل از خرید حتماً تست کنید یا از گارانتی تعویض مطمئن شوید.</p>
<p>مشاهده محصولات: <a href="/category/handsfree/">هندزفری و ایربادز</a></p>
""",
    },
    {
        "slug": "phone-case-glass",
        "title": "قاب و گلس؛ محافظتی که واقعاً کار می‌کند",
        "excerpt": "چطور بین قاب سیلیکونی، سخت و گلس پرایوسی یکی را انتخاب کنید.",
        "category": "guides",
        "tags": ["قاب", "گلس"],
        "image": "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?auto=format&fit=crop&w=1200&q=80",
        "days_ago": 8,
        "content": """
<p>گلس بدون قاب کامل نیست و قاب بدون گلس هم جلوی خط‌وخش صفحه را نمی‌گیرد. ترکیب پیشنهادی لونا سنتر:</p>
<ul>
<li>قاب سیلیکونی نرم برای استفاده روزمره</li>
<li>گلس با پوشش مناسب لبه برای مدل‌های لبه‌گرد</li>
<li>گلس پرایوسی اگر معمولاً در مترو و تاکسی کار می‌کنید</li>
</ul>
<p>محصولات مرتبط در <a href="/category/cases/">قاب و گلس</a> موجود است.</p>
""",
    },
    {
        "slug": "tablet-for-study",
        "title": "تبلت برای درس و کار سبک؛ چه مدلی بخریم؟",
        "excerpt": "تبلت میان‌رده برای مطالعه PDF، کلاس آنلاین و یادداشت‌برداری.",
        "category": "guides",
        "tags": ["تبلت", "راهنمای خرید"],
        "image": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=1200&q=80",
        "days_ago": 12,
        "content": """
<p>برای دانشجو و کارمند دورکار، تبلت باید سبک، با باتری خوب و صفحه‌نمایش خوانا باشد. رم ۴ به بالا و حافظه قابل ارتقا امتیاز مهمی است.</p>
<p>اگر فقط وبگردی و مطالعه می‌خواهید، سری Tab A گزینه اقتصادی است؛ برای کار سنگین‌تر به سری بالاتر فکر کنید.</p>
<p><a href="/category/tablet/">مشاهده تبلت‌ها</a></p>
""",
    },
    {
        "slug": "lona-shipping-payment",
        "title": "ارسال و پرداخت در لونا سنتر چگونه است؟",
        "excerpt": "پست، تیپاکس، درگاه امن و نکات قبل از ثبت سفارش.",
        "category": "news",
        "tags": ["لونا سنتر", "ارسال"],
        "image": "https://images.unsplash.com/photo-1572569511254-d8f925fe2cbb?auto=format&fit=crop&w=1200&q=80",
        "days_ago": 15,
        "content": """
<p>در لونا سنتر سفارش‌ها با <strong>پست</strong> یا <strong>تیپاکس</strong> ارسال می‌شوند و پرداخت از طریق درگاه امن انجام می‌گیرد.</p>
<p>قبل از ثبت نهایی:</p>
<ul>
<li>آدرس و کدپستی را دقیق وارد کنید</li>
<li>موجودی و رنگ/حافظه انتخابی را در صفحه محصول چک کنید</li>
<li>در صورت نیاز به مشاوره، از صفحه تماس پیام بگذارید</li>
</ul>
<p>خرید راحت از <a href="/category/">فروشگاه</a> شروع می‌شود.</p>
""",
    },
]

CATEGORIES = [
    ("guides", "راهنمای خرید", "آموزش و راهنمای انتخاب محصول"),
    ("reviews", "بررسی و مقایسه", "مقایسه کاربردی محصولات"),
    ("news", "اخبار فروشگاه", "اطلاعیه‌ها و به‌روزرسانی‌های لونا سنتر"),
]


class Command(BaseCommand):
    help = "افزودن مقالات وبلاگ لونا سنتر"

    def handle(self, *args, **options):
        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("فروشگاه shop1 پیدا نشد."))
            return

        plugin, _ = Plugin.objects.get_or_create(
            codename="blog",
            defaults={"name": "Blog", "description": "Blog and articles", "is_active": True},
        )
        StorePlugin.objects.update_or_create(
            store=store, plugin=plugin, defaults={"is_enabled": True}
        )

        cats = {}
        for slug, name, desc in CATEGORIES:
            cat, _ = BlogCategory.objects.update_or_create(
                store=store,
                slug=slug,
                defaults={"name": name, "description": desc, "is_active": True},
            )
            cats[slug] = cat

        tag_cache = {}
        for post in POSTS:
            for name in post["tags"]:
                if name not in tag_cache:
                    slug = name.replace(" ", "-")
                    tag, _ = BlogTag.objects.get_or_create(
                        store=store, slug=slug, defaults={"name": name}
                    )
                    tag_cache[name] = tag

        author = User.objects.filter(is_superuser=True).first() or User.objects.first()
        now = timezone.now()
        created_n = updated_n = 0

        for row in POSTS:
            published_at = now - timedelta(days=row["days_ago"])
            post, created = BlogPost.objects.update_or_create(
                store=store,
                slug=row["slug"],
                defaults={
                    "title": row["title"],
                    "excerpt": row["excerpt"],
                    "content": row["content"].strip(),
                    "category": cats[row["category"]],
                    "author": author,
                    "featured_image": row["image"],
                    "is_published": True,
                    "published_at": published_at,
                    "meta_title": row["title"][:70],
                    "meta_description": row["excerpt"][:160],
                },
            )
            post.tags.set([tag_cache[n] for n in row["tags"]])
            if created:
                created_n += 1
            else:
                updated_n += 1
            self.stdout.write(("+" if created else "~") + f" {post.slug}")

        # Soft-hide generic welcome demo if present
        BlogPost.objects.filter(store=store, slug="welcome").update(is_published=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"وبلاگ لونا سنتر آماده: {created_n} جدید، {updated_n} به‌روز، مجموع={len(POSTS)}"
            )
        )
