# طرق ورود (Authentication)

این سند روش‌های ورود به ShopCMS را توضیح می‌دهد.

---

## خلاصه

| روش | مخاطب | صفحه / مسیر | نوع احراز هویت |
|------|--------|-------------|----------------|
| OTP با موبایل | مشتری، ادمین فروشگاه، سوپرادمین | `/login/` ، `/register/` | کد یک‌بارمصرف + JWT (+ سشن) |
| Django Admin | سوپرادمین / staff با پسورد | `/admin/` | شماره موبایل + رمز عبور |
| TOTP (۲FA) | کاربرانی که ۲FA فعال دارند | API بعد از OTP | کد اپلیکیشن احراز هویت |

**وجود ندارد:** ورود با ایمیل/یوزرنیم در فروشگاه، رمز عبور در `/login/`، یا OAuth / ورود با گوگل و شبکه‌های اجتماعی.

---

## ۱. ورود با OTP (روش اصلی)

همان صفحه برای مشتری و ادمین فروشگاه استفاده می‌شود.

### صفحات

| مسیر | کاربرد |
|------|--------|
| `/login/` | ورود |
| `/login/?next=/manage/` | ورود و هدایت به پنل مدیریت فروشگاه |
| `/register/` | ثبت‌نام مشتری در بستر فروشگاه فعلی |

### جریان کار

1. کاربر شماره موبایل را وارد می‌کند (`09xxxxxxxxx`).
2. سیستم OTP پنج‌رقمی می‌فرستد (انقضا حدود ۲ دقیقه).
3. با تأیید OTP:
   - جفت توکن JWT صادر می‌شود (در `sessionStorage`).
   - سشن Django هم ساخته می‌شود.
4. هدایت بعدی:
   - staff / سوپرادمین ← معمولاً `/manage/`
   - مشتری ← `/dashboard/` (یا مقدار `?next=`)

### API مرتبط

پایه: `/api/v1/auth/`  
مستندات Swagger: `http://localhost:8000/api/v1/docs`

| Method | Path | توضیح |
|--------|------|--------|
| `POST` | `/api/v1/auth/otp/send` | ارسال OTP — `purpose`: `login` یا `register` |
| `POST` | `/api/v1/auth/otp/verify/login` | تأیید ورود → توکن‌ها (یا چالش ۲FA با HTTP 202) |
| `POST` | `/api/v1/auth/otp/verify/register` | تأیید ثبت‌نام (نیاز به کانتکست فروشگاه) |
| `POST` | `/api/v1/auth/token/refresh` | تمدید access token |
| `POST` | `/api/v1/auth/logout` | خروج و blacklist شدن refresh |
| `GET` | `/api/v1/auth/me` | پروفایل کاربر فعلی (JWT) |

### محدودیت‌های OTP

- طول کد: ۵ رقم  
- انقضا: حدود ۲ دقیقه  
- حداکثر تلاش تأیید: ۵ بار  
- فاصله ارسال مجدد: در production معمولاً ۱ بار در ۶۰ ثانیه برای هر شماره؛ در development تا ۱۰ بار در دقیقه مجاز است  

اگر خطای «Too many requests» / محدودیت درخواست دیدید، حدود یک دقیقه صبر کنید یا سرور dev را یک‌بار restart کنید تا cache محدودیت پاک شود.

پیاده‌سازی: `accounts/services/otp.py`

### محیط توسعه

در `development` و `test` کد ثابت فعال است:

```
OTP_USE_FIXED_CODE=True
OTP_FIXED_CODE=12345
```

یعنی هر شماره‌ای با OTP **`12345`** وارد می‌شود (بدون ارسال واقعی SMS).

ادمین نمونه (بعد از `seed_store_admin`):

| فیلد | مقدار |
|------|--------|
| موبایل | `09120000000` |
| OTP در dev | `12345` |
| نقش | `store_admin` روی فروشگاه نمونه (`shop1`) |

---

## ۲. پنل مدیریت فروشگاه (Store Admin)

ورود جداگانه ندارد؛ همان OTP از `/login/` است.

| مورد | جزئیات |
|------|--------|
| آدرس پنل | `/manage/` |
| صفحات | محصولات، سفارش‌ها، تنظیمات و … زیر `/manage/…` |
| دسترسی صفحه HTML | سشن Django + چک نقش staff فروشگاه |
| دسترسی API | JWT با هدر `Authorization: Bearer …` روی `/api/v1/store-admin/*` |

نقش‌های رایج: `store_admin`، `manager`، `content`، `products`، `orders`، `reports`، `support`  
سوپرادمین پلتفرم هم به APIهای store-admin دسترسی دارد.

ساختن کاربر نمونه:

```powershell
python manage.py seed_store_admin
```

سپس:

```
http://localhost:8000/login/?next=/manage/
```

موبایل `09120000000` و OTP `12345`.

---

## ۳. سوپرادمین پلتفرم (Super Admin)

| مورد | جزئیات |
|------|--------|
| ورود UI فروشگاه | همان `/login/` با OTP |
| API | `/api/v1/super-admin/*` — فقط JWT + `is_superuser` |
| ساخت کاربر | `python manage.py createsuperuser` (فیلد اصلی: **شماره موبایل**) |

برای پنل داخلی Django هم پسورد لازم است (بخش بعد).

---

## ۴. Django Admin (ورود با رمز عبور)

تنها مسیر ورود مبتنی بر **پسورد** در پروژه.

| مورد | جزئیات |
|------|--------|
| آدرس | `http://localhost:8000/admin/` |
| شناسه ورود | شماره موبایل (`USERNAME_FIELD` مدل User) |
| رمز | پسوردی که هنگام `createsuperuser` یا در ادمین ست شده |

کاربرانی که فقط با OTP ساخته شده‌اند معمولاً پسورد قابل‌استفاده ندارند مگر جداگانه ست شود.

---

## ۵. احراز هویت دومرحله‌ای (TOTP / 2FA)

بعد از OTP، اگر ۲FA برای کاربر فعال باشد:

1. پاسخ `otp/verify/login` با **HTTP 202** و `challenge_token`
2. تأیید کد اپلیکیشن: `POST /api/v1/auth/2fa/verify`
3. سپس توکن‌های نهایی صادر می‌شود

APIهای مدیریت ۲FA (نیاز به JWT):

| Path | کار |
|------|-----|
| `/api/v1/auth/2fa/setup` | شروع راه‌اندازی |
| `/api/v1/auth/2fa/enable` | فعال‌سازی |
| `/api/v1/auth/2fa/disable` | غیرفعال‌سازی |

> UI فعلی صفحه `/login/` ممکن است سناریوی ۲۰۲/۲FA را کامل پوشش ندهد؛ جریان در لایه API پیاده شده است.

---

## ۶. JWT و سشن (ساز و کار، نه روش ورود جدا)

بعد از ورود موفق:

| مورد | مقدار تقریبی |
|------|----------------|
| Access token | حدود ۱۵ دقیقه |
| Refresh token | حدود ۷ روز |
| ذخیره‌سازی سمت کلاینت | `sessionStorage` (+ سشن سرور برای صفحات HTML) |

خیلی از APIهای مشتری هم Bearer و هم سشن Django را می‌پذیرند.  
پنل `/manage/` صفحات را با سشن و داده‌ها را با JWT لود می‌کند.

---

## نقشه سریع دسترسی‌ها

```
مشتری          →  /login/ (OTP)  →  /dashboard/
ادمین فروشگاه  →  /login/?next=/manage/ (OTP)  →  /manage/
سوپرادمین      →  /login/ (OTP) و/یا /admin/ (پسورد)
API همه        →  Bearer JWT پس از OTP (+ در صورت نیاز 2FA)
```

---

## فایل‌های مهم

| مسیر | نقش |
|------|------|
| `static/js/auth.js` | UI ورود/ثبت‌نام OTP |
| `themes/default/auth.html` | تمپلیت صفحه ورود |
| `accounts/api/auth.py` | endpointهای auth |
| `accounts/services/otp.py` | منطق OTP |
| `accounts/services/jwt.py` | صدور/تمدید توکن |
| `accounts/services/two_factor.py` | TOTP |
| `dashboard/authentication_store.py` | دسترسی store-admin |
| `dashboard/authentication.py` | دسترسی super-admin |
| `accounts/management/commands/seed_store_admin.py` | کاربر ادمین نمونه |
| `tenants/urls.py` | مسیرهای `/login/` و `/manage/` |

---

## لینک‌های مرتبط

- اجرای لوکال: [LOCAL_SETUP.md](LOCAL_SETUP.md)
- خلاصه سریع اجرا: [RUN.md](RUN.md)
