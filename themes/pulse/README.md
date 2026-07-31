# Pulse Theme

فروانت‌اند مدرن استورفرانت با:

- **Vite** — باندل و build
- **Tailwind CSS v4** — استایل utility + کامپوننت‌های تم
- **Lucide** — آیکون‌ها
- **GSAP** — انیمیشن اسکرول/Reveal
- **Swiper** — اسلایدر و کاروسل محصولات
- **HTMX** — در دسترس به‌صورت `window.htmx` برای تعاملات جزئی

## توسعه

```bash
cd themes/pulse
npm install
npm run dev      # یا
npm run build    # خروجی در static/themes/pulse/
```

## فعال‌سازی

1. `python manage.py seed_store` (تم `pulse` را ثبت می‌کند)
2. در ادمین، تم فروشگاه را روی **Pulse** بگذارید

یا در شل:

```python
from tenants.models import Store, Theme
t = Theme.objects.get(slug="pulse")
Store.objects.filter(slug="shop1").update(theme=t)
```
