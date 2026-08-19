# 09 — Dev, seeds, Docker, tests

Project root: `D:\DEVLIC\ShopCMS\app`  
`manage.py` uses `config.settings.development` unless env overrides.

## Local (SQLite, no Redis) — daily path

```powershell
cd D:\DEVLIC\ShopCMS\app
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements\development.txt
Copy-Item .env.example .env
# DATABASE_URL=sqlite:///db.sqlite3
# OTP_USE_FIXED_CODE=True  OTP_FIXED_CODE=12345  DEFAULT_STORE_SLUG=shop1
python manage.py migrate
```

Seeds (order matters for FKs):

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
python manage.py runserver
```

Optional: `createsuperuser` (asks for **phone**, not username).

### URLs after seed

| URL | What |
|-----|------|
| http://localhost:8000/ | shop1 storefront |
| http://localhost:8000/manage/ | store admin |
| http://localhost:8000/admin/ | Unfold |
| http://localhost:8000/api/v1/docs | Swagger |

Admin sample: `09120000000` / OTP `12345`.

Development `ALLOWED_HOSTS` includes `.local` (e.g. `gohar.local`, `shop1.local`). Map hosts file if needed.

### Extra seeds

| Command | Purpose |
|---------|---------|
| `seed_gohar` | Gohar jewelry store + catalog + menus |
| `seed_lonacenter` / `seed_lonacenter_cms` / `seed_lonacenter_pages` / `seed_lonacenter_blog` | Lona Center / nextshop-oriented content |
| `merge_color_attributes` | catalog cleanup |
| `expire_subscriptions` | also a Celery beat task |

Ops commands: `backup_store`, `backup_platform`, `restore_store`, `export_docker_seed`, `clear_cache`, `warm_cache`.

## Vite (pulse / gohar)

```powershell
cd themes\pulse   # or themes\gohar
npm install
npm run build     # → static/themes/<name>/
```

## Tests

`pytest.ini`: `DJANGO_SETTINGS_MODULE=config.settings.test`

```powershell
pytest
pytest --cov=.
```

`testpaths` include every Django app plus `tests/`.

## Docker

| File | Role |
|------|------|
| `docker/docker-compose.yml` | dev: runserver, celery, beat, postgres, redis |
| `docker/docker-compose.staging.yml` | nginx:80, gunicorn, seed loaddata/media |
| `docker/docker-compose.prod.yml` | nginx, gunicorn, celery worker/beat, postgres, redis |
| `docker/Dockerfile`, `entrypoint.sh`, `gunicorn.conf.py`, `docker/nginx/` | |

```bash
docker compose -f docker/docker-compose.yml up --build
```

Staging export from local DB+media:

```
python manage.py export_docker_seed
# → docker/seed-data/data.json + docker/seed-data/media/
```

Health: `/api/v1/health/live|ready|/|metrics`

## Celery Beat (Tehran)

| Task | When |
|------|------|
| expire_subscriptions | 02:00 daily |
| cleanup_temp_files | hourly |
| warm_active_stores_cache | every 6h at :15 |
| backup_active_stores | 03:30 daily |
| cleanup_old_backups | Sunday 04:00 |
| cleanup_audit_logs | Sunday 04:30 |

Local runserver does **not** need Celery for browsing/cart/checkout (except background jobs).

## CI

`.github/workflows/ci.yml` — migrate check, pytest, docker build on main.

## Requirements files

- `requirements/base.txt` — Django 5.0–5.2, ninja, unfold, whitenoise, psycopg2, redis, celery, pydantic, PyJWT, Pillow, pyotp
- `requirements/development.txt` — base + debug/test extras
- `requirements/production.txt`
