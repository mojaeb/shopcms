# راهنمای اجرای ShopCMS روی لوکال

این سند برای اجرای پروژه روی ویندوز (و مشابه آن روی لینوکس/مک) نوشته شده است.

مسیر پروژه:

```
D:\DEVLIC\ShopCMS\app
```

---

## پیش‌نیازها

| ابزار | نسخه پیشنهادی | الزامی |
|--------|----------------|--------|
| Python | 3.10 یا بالاتر | بله |
| Git | هر نسخه اخیر | بله |
| Docker Desktop | اخیر | فقط برای روش Docker |
| PostgreSQL / Redis | — | فقط اگر بدون Docker و با Postgres بخواهید |

---

## روش ۱ — سریع (بدون Docker، با SQLite)

مناسب برای توسعه روزمره. نیازی به نصب Postgres و Redis نیست.

### ۱. کلون و ورود به پوشه

```powershell
cd D:\DEVLIC\ShopCMS\app
```

### ۲. ساخت محیط مجازی

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

اگر PowerShell اجازه اجرای اسکریپت نداد:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### ۳. نصب وابستگی‌ها

```powershell
pip install -r requirements\development.txt
```

### ۴. تنظیم فایل `.env`

```powershell
Copy-Item .env.example .env
```

فایل `.env` را باز کنید و حداقل این موارد را تنظیم کنید:

```env
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=یک-رشته-تصادفی-طولانی
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# SQLite برای توسعه ساده (بدون Postgres)
DATABASE_URL=sqlite:///db.sqlite3

OTP_USE_FIXED_CODE=True
OTP_FIXED_CODE=12345
DEFAULT_STORE_SLUG=shop1
```

> در حالت `development` کش از **LocMem** استفاده می‌کند؛ Redis برای اجرای معمولی سرور لازم نیست.

### ۵. مایگریشن دیتابیس

```powershell
python manage.py migrate
```

### ۶. داده‌های اولیه (Seed)

```powershell
python manage.py seed_store
python manage.py seed_roles
python manage.py seed_store_admin
python manage.py seed_plugins
python manage.py seed_cms
python manage.py seed_products
python manage.py seed_coupons
python manage.py seed_shipping
python manage.py seed_payments
python manage.py seed_taxes
python manage.py seed_wishlists
python manage.py seed_comments
python manage.py seed_blog
python manage.py seed_files
python manage.py seed_notifications
python manage.py seed_digital
python manage.py seed_subscriptions
```

یا یک‌جا (PowerShell):

```powershell
@(
  "seed_store","seed_roles","seed_store_admin","seed_plugins","seed_cms","seed_products",
  "seed_coupons","seed_shipping","seed_payments","seed_taxes","seed_wishlists",
  "seed_comments","seed_blog","seed_files","seed_notifications","seed_digital","seed_subscriptions"
) | ForEach-Object { python manage.py $_ }
```
### ۷. ساخت سوپرادمین (اختیاری — برای `/admin/`)

```powershell
python manage.py createsuperuser
```

- **شماره موبایل** به‌جای username پرسیده می‌شود (مثلاً `09120000000`)
- رمز عبور دلخواه

### ۸. اجرای سرور

```powershell
python manage.py runserver
```

سرور روی آدرس زیر بالا می‌آید:

```
http://127.0.0.1:8000
```

---

## روش ۲ — با Docker (Postgres + Redis + Celery)

مناسب وقتی می‌خواهید محیط نزدیک به production داشته باشید.

### ۱. آماده‌سازی `.env`

```powershell
cd D:\DEVLIC\ShopCMS\app
Copy-Item .env.example .env
```

در `.env` مقدار `DATABASE_URL` را برای Docker نگه دارید (یا همان پیش‌فرض Postgres):

```env
DATABASE_URL=postgres://shopcms:shopcms@localhost:5432/shopcms
```

### ۲. اجرای سرویس‌ها

```powershell
cd docker
docker compose up --build
```

سرویس‌های بالا آمده:
- **web** — Django روی پورت `8000`
- **db** — PostgreSQL روی `5432`
- **redis** — Redis روی `6379`
- **celery** و **celery-beat** — تسک‌های پس‌زمینه

### ۳. مایگریشن و Seed (داخل کانتینر)

در ترمینال دیگر:

```powershell
cd D:\DEVLIC\ShopCMS\app\docker
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_store
docker compose exec web python manage.py seed_roles
# ... بقیه seedها مثل روش ۱
```

### ۴. توقف

```powershell
docker compose down
```

---

## آدرس‌های مهم بعد از اجرا

| آدرس | توضیح |
|------|--------|
| http://localhost:8000/ | فروشگاه (storefront) — فروشگاه `shop1` |
| http://localhost:8000/manage/ | پنل Store Admin (داشبورد، محصولات، سفارشات، تنظیمات) |
| http://localhost:8000/login/?next=/manage/ | ورود به پنل مدیریت |
| http://localhost:8000/login/ | ورود مشتری / ادمین |
| http://localhost:8000/register/ | ثبت‌نام |
| http://localhost:8000/admin/ | پنل Django Admin |
| http://localhost:8000/api/v1/docs | مستندات Swagger API |
| http://localhost:8000/api/v1/health/ | وضعیت سلامت سیستم |

### Multi-tenant

پس از `seed_store`، این دامنه‌ها به فروشگاه `shop1` وصل می‌شوند:

- `localhost`
- `127.0.0.1`
- `shop1.local`

برای تست با دامنه سفارشی، در فایل hosts ویندوز (`C:\Windows\System32\drivers\etc\hosts`) اضافه کنید:

```
127.0.0.1 shop1.local
```

---

## ورود با OTP (توسعه)

وقتی در `.env` این تنظیم فعال است:

```env
OTP_USE_FIXED_CODE=True
OTP_FIXED_CODE=12345
```

برای ورود:

1. به `/login/` بروید
2. شماره موبایلی که قبلاً ثبت شده را وارد کنید
3. کد OTP را `12345` بگذارید

برای **ادمین فروشگاه** بعد از `seed_store_admin`:

1. به http://localhost:8000/login/?next=/manage/ بروید
2. شماره `09120000000` را وارد کنید
3. کد OTP را `12345` بگذارید
4. به پنل `/manage/` هدایت می‌شوید

برای **ثبت‌نام مشتری جدید** از `/register/` استفاده کنید؛ همان کد ثابت کار می‌کند.

### ورود به API (مثال)

```http
POST http://localhost:8000/api/v1/auth/otp/send
Content-Type: application/json
Host: localhost

{"phone": "09121111111", "purpose": "login"}
```

```http
POST http://localhost:8000/api/v1/auth/otp/verify/login
Content-Type: application/json
Host: localhost

{"phone": "09121111111", "code": "12345"}
```

---

## اجرای تست‌ها

```powershell
cd D:\DEVLIC\ShopCMS\app
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL="sqlite:///db.sqlite3"
$env:SECRET_KEY="test-key"
pytest
```

با گزارش coverage:

```powershell
pytest --cov=. --cov-report=term-missing
```

---

## Celery (اختیاری — بدون Docker)

اگر Redis نصب دارید و می‌خواهید تسک‌های پس‌زمینه اجرا شوند:

**ترمینال ۱ — Worker:**

```powershell
celery -A config worker -l info
```

**ترمینال ۲ — Beat (زمان‌بندی):**

```powershell
celery -A config beat -l info
```

بدون Celery هم سرور و API به‌طور عادی کار می‌کنند؛ فقط jobهای زمان‌بندی‌شده (بکاپ شبانه، expire اشتراک و ...) اجرا نمی‌شوند.

---

## مشکلات رایج

### `No module named 'django'`

محیط مجازی فعال نیست:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements\development.txt
```

### `فروشگاه یافت نشد` (404)

- حتماً `seed_store` را اجرا کنید
- از `localhost` یا `127.0.0.1` استفاده کنید
- `DEFAULT_STORE_SLUG=shop1` در `.env` باشد

### خطای دیتابیس Postgres

- یا Docker را بالا بیاورید
- یا در `.env` بگذارید: `DATABASE_URL=sqlite:///db.sqlite3`

### پوشه `staticfiles` وجود ندارد

برای توسعه معمولاً مشکلی نیست. در صورت نیاز:

```powershell
python manage.py collectstatic --noinput
```

### پورت 8000 اشغال است

```powershell
python manage.py runserver 8001
```

---

## خلاصه دستورات (کپی سریع)

```powershell
cd D:\DEVLIC\ShopCMS\app
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements\development.txt
Copy-Item .env.example .env
# DATABASE_URL=sqlite:///db.sqlite3 را در .env تنظیم کنید
python manage.py migrate
python manage.py seed_store
python manage.py seed_roles
python manage.py seed_store_admin
python manage.py seed_plugins
python manage.py seed_cms
python manage.py seed_products
python manage.py runserver
```

سپس باز کنید:
- فروشگاه: **http://localhost:8000/**
- پنل Store Admin: **http://localhost:8000/manage/** (ادمین: `09120000000` / OTP: `12345`)

---

برای deploy روی سرور واقعی، فایل [DEPLOYMENT.md](./DEPLOYMENT.md) را ببینید.
