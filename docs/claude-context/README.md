# بستهٔ زمینه برای Claude — ShopCMS

این پوشه یک **handoff کامل** از پروژه ShopCMS است. هدف: دادن آن به Claude (یا هر مدل دیگر) تا بدون گشتن در کل ریپو بتواند به سوالات معماری، تم، API، سبد/تسویه، احراز هویت و توسعه پاسخ بدهد.

## چطور به Claude بدهید

### روش پیشنهادی
1. کل پوشه `docs/claude-context/` را به چت ضمیمه کنید (یا محتویات را پیست کنید).
2. اول این جمله را بفرستید:

```
You are helping with ShopCMS, a Persian RTL multi-tenant Django 5 commerce platform.
Read docs/claude-context/00-START-HERE.md first, then answer from the other files in that folder.
If a file path is mentioned, prefer reading the real source in the repo when available.
```

3. بعد سوال‌تان را بپرسید (مثلاً «چرا سبد خالی رندر نمی‌شود» یا «چطور تم جدید بسازم»).

### اگر محدودیت حجم دارید
حداقل این فایل‌ها را بدهید:
1. `00-START-HERE.md`
2. `01-overview.md`
3. فایل مرتبط با سوال:
   - تم / HTML / CSS / JS → `05-storefront-themes.md`
   - سبد / تسویه / پرداخت → `06-commerce-flows.md`
   - API → `04-api.md`
   - مدل‌ها / دیتابیس → `03-domain-models.md`
   - ورود / نقش‌ها → `07-auth.md`
   - اجرا / Docker / تست → `09-dev-ops.md`

## این بسته چیست / چیست نیست

**هست:** نقشه ذهنی پروژه، قراردادهای تم و JS، لیست API، مدل دامنه، جریان خرید، قوانین کدنویسی، مسیر فایل‌های مهم.

**نیست:** کل سورس‌کد، secrets، `.env` واقعی، لاگ، media، `node_modules`. اگر Claude باید کد را تغییر دهد، ریپوی واقعی را هم باید ببیند.

تاریخ تولید: ۱۶ اوت ۲۰۲۶.
مسیر پروژه: `D:\DEVLIC\ShopCMS\app`
