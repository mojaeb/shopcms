"""Seed About + Contact CMS pages for Lona Center (shortcode-based content)."""

from django.core.management.base import BaseCommand

from cms.enums import MenuLocation
from cms.models import Menu, MenuItem, Page
from cms.services.cache import CMSCacheService
from cms.services.shortcodes import invalidate_shortcode_cache
from tenants.models import Store

ABOUT_CONTENT = """
[split image="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=1400&q=80" alt="فضای مشاوره خرید لونا سنتر"]
[lead text="لونا سنتر فروشگاه تخصصی موبایل، تبلت و لوازم جانبی اصل است — با تمرکز روی انتخاب درست، قیمت شفاف و پشتیبانی واقعی از مشاوره تا بعد از تحویل."/]
[cta label="مشاهده محصولات" href="/products/"/]
[/split]

[section tone="soft"]
[heading title="چرا لونا سنتر؟" text="سه اصل ساده برای خریدی مطمئن"/]
[grid-1-3]
[feature icon="badge-check" title="اصالت کالا" text="محصولات با گارانتی معتبر و فاکتور رسمی؛ بدون کالای متفرقه و مبهم."/]
[feature icon="tag" title="قیمت شفاف" text="رقابتی نسبت به بازار، بدون هزینه پنهان در لحظه پرداخت."/]
[feature icon="headphones" title="پشتیبانی واقعی" text="راهنمایی تخصصی برای انتخاب گوشی، تبلت و لوازم جانبی."/]
[/grid-1-3]
[/section]

[section tone="plain"]
[heading title="چطور خرید می‌کنید؟" text="از انتخاب تا تحویل، مسیر مشخص و قابل پیگیری"/]
[grid-1-2]
[feature icon="smartphone" title="انتخاب با اطمینان" text="مدل، حافظه و رنگ را ببینید؛ اگر مردد بودید قبل از خرید با پشتیبانی هماهنگ کنید."/]
[feature icon="truck" title="ارسال و پیگیری" text="ارسال با پست و تیپاکس به سراسر کشور؛ وضعیت سفارش از حساب کاربری قابل مشاهده است."/]
[/grid-1-2]
[prose text="از گوشی‌های پرچمدار تا پاوربانک، شارژر، قاب و گلس — تیم لونا سنتر کنار شماست تا خریدی سریع و شفاف داشته باشید."/]
[note text="هدف ما ساده است: انتخاب درست، تحویل به‌موقع، و همراهی بعد از فروش."/]
[/section]

[section tone="cta"]
[heading title="آماده خرید هستید؟" text="کاتالوگ به‌روز موبایل و لوازم جانبی را ببینید"/]
[cta label="ورود به فروشگاه" href="/products/"/]
[/section]
""".strip()

CONTACT_CONTENT = """
[section tone="soft"]
[heading title="راه‌های ارتباطی" text="یکی را انتخاب کنید؛ برای پاسخ سریع‌تر شماره سفارش یا مدل کالا را بنویسید"/]
[grid-1-2]
[contact-item icon="phone" label="تلفن پشتیبانی" value="۰۲۱-۹۱۰۹۱۰۹۱" href="tel:+982191091091"/]
[contact-item icon="message-circle" label="واتساپ" value="۰۹۱۲ ۱۲۳ ۴۵۶۷" href="https://wa.me/989121234567"/]
[contact-item icon="mail" label="ایمیل" value="info@lonacenter.ir" href="mailto:info@lonacenter.ir"/]
[contact-item icon="map-pin" label="آدرس فروشگاه" value="تهران، خیابان ولیعصر، نبش خیابان طالقانی" href="https://maps.google.com/?q=Tehran+Valiasr"/]
[/grid-1-2]
[/section]

[section tone="plain"]
[heading title="قبل از تماس بدانید" text=""/]
[grid-1-3]
[feature icon="clock" title="ساعات پاسخ‌گویی" text="شنبه تا پنج‌شنبه ۹ تا ۱۸ — جمعه‌ها تعطیل"/]
[feature icon="package" title="پیگیری سفارش" text="از حساب کاربری، بخش سفارش‌ها وضعیت ارسال را ببینید."/]
[feature icon="help-circle" title="راهنمای خرید" text="قبل از خرید، مدل و موجودی را با پشتیبانی هماهنگ کنید."/]
[/grid-1-3]
[note text="برای پاسخ سریع‌تر، شماره سفارش یا مدل کالا را در پیام خود ذکر کنید."/]
[/section]

[section tone="cta"]
[heading title="همین حالا خرید را شروع کنید" text="یا اگر سوال دارید از راه‌های بالا پیام بگذارید"/]
[cta label="مشاهده محصولات" href="/products/"/]
[/section]
""".strip()


class Command(BaseCommand):
    help = "صفحات درباره ما و تماس با ما لونا سنتر را با شورت‌کد پر می‌کند"

    def handle(self, *args, **options):
        store = Store.objects.filter(slug="shop1").first()
        if not store:
            self.stdout.write(self.style.WARNING("Store shop1 not found."))
            return

        about, _ = Page.objects.update_or_create(
            store=store,
            slug="about",
            defaults={
                "title": "درباره ما",
                "content": ABOUT_CONTENT,
                "meta_title": "درباره لونا سنتر",
                "meta_description": "لونا سنتر؛ فروشگاه تخصصی موبایل، تبلت و لوازم جانبی اصل با ضمانت، قیمت شفاف و پشتیبانی واقعی.",
                "is_published": True,
            },
        )

        contact, _ = Page.objects.update_or_create(
            store=store,
            slug="contact",
            defaults={
                "title": "تماس با ما",
                "content": CONTACT_CONTENT,
                "meta_title": "تماس با لونا سنتر",
                "meta_description": "تلفن، واتساپ، ایمیل و آدرس لونا سنتر برای مشاوره خرید و پیگیری سفارش.",
                "is_published": True,
            },
        )

        header_menu, _ = Menu.objects.get_or_create(
            store=store,
            location=MenuLocation.HEADER,
            defaults={"name": "Header Menu", "is_active": True},
        )
        for label, url, order in (
            ("درباره ما", f"/page/{about.slug}/", 20),
            ("تماس با ما", f"/page/{contact.slug}/", 21),
            ("محصولات", "/products/", 5),
        ):
            item, created = MenuItem.objects.get_or_create(
                menu=header_menu,
                label=label,
                defaults={"url": url, "sort_order": order, "is_active": True},
            )
            if not created:
                changed = False
                if label == "محصولات" and "/category/" in (item.url or ""):
                    item.url = "/products/"
                    changed = True
                if item.url != url and label in ("درباره ما", "تماس با ما"):
                    item.url = url
                    changed = True
                if changed:
                    item.save(update_fields=["url"])

        CMSCacheService().invalidate_store(store)
        invalidate_shortcode_cache(store)

        self.stdout.write(self.style.SUCCESS(
            f"Updated pages: /page/{about.slug}/ and /page/{contact.slug}/"
        ))
