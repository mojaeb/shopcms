فایل راهنما اینجاست:

**[docs/LOCAL_SETUP.md](d:\DEVLIC\ShopCMS\app\docs\LOCAL_SETUP.md)**

### خلاصه سریع

**روش ساده (پیشنهادی برای شروع):**

```powershell
cd D:\DEVLIC\ShopCMS\app
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements\development.txt
Copy-Item .env.example .env
```

در `.env` بگذارید: `DATABASE_URL=sqlite:///db.sqlite3`

```powershell
python manage.py migrate
python manage.py seed_store
python manage.py seed_roles
python manage.py seed_plugins
python manage.py seed_cms
python manage.py seed_products
python manage.py seed_store_admin
python manage.py runserver
```

بعد باز کنید:
- فروشگاه: **http://localhost:8000/**
- پنل Store Admin: **http://localhost:8000/manage/**

تم‌ها: `default` / `modern` / `minimal` / `round` (ظاهر Sellzy با گوشه‌های گرد)

ادمین نمونه: شماره **`09120000000`** — OTP: **`12345`**

ورود مشتری با OTP در توسعه: کد ثابت **`12345`**

طرق کامل ورود (OTP، پنل manage، Django Admin، 2FA): **[docs/AUTH.md](AUTH.md)**

---

در همان فایل این‌ها هم هست:
- روش Docker (Postgres + Redis + Celery)
- لیست کامل seedها
- آدرس‌های API و storefront / manage
- اجرای تست‌ها
- رفع مشکلات رایج
