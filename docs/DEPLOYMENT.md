# ShopCMS Deployment Guide

## Quick start (development)

```bash
cp .env.example .env
pip install -r requirements/development.txt
python manage.py migrate
python manage.py seed_store
python manage.py runserver
```

Or with Docker:

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Staging / test server (با داده و رسانهٔ فعلی)

روی ماشین لوکال (با دیتابیس و media فعلی):

```bash
# از ریشهٔ پروژه
.venv\Scripts\python.exe manage.py export_docker_seed
# → می‌سازد: docker/seed-data/data.json + docker/seed-data/media/
```

روی سرور امتحانی:

```bash
# کل پروژه را کپی کنید (حتماً پوشه docker/seed-data هم باشد)
cp docker/.env.staging.example .env.staging
# SECRET_KEY و ALLOWED_HOSTS را ویرایش کنید

docker compose -f docker/docker-compose.staging.yml --env-file .env.staging up --build -d
```

Stack: **Nginx :80**, Gunicorn, Celery, Postgres, Redis.  
در اولین بالا آمدن: migrate → `loaddata` از `seed-data/data.json` → کپی media.

فروشگاه‌ها (در صورت seed فعلی):

| فروشگاه | Host نمونه |
|---------|------------|
| لونا / shop1 | IP سرور یا `shop1.<domain>` |
| گوهر | `gohar.<domain>` یا `/` با دامنهٔ ست‌شده در پنل |

دامنه‌های Tenant را در پنل یا با `ALLOWED_HOSTS=*` (پیش‌فرض staging) باز کنید. برای OTP تست: `OTP_USE_FIXED_CODE=True` و کد `12345`.

بازنشانی seed (دیتابیس خالی):

```bash
docker compose -f docker/docker-compose.staging.yml --env-file .env.staging down -v
docker compose -f docker/docker-compose.staging.yml --env-file .env.staging up --build -d
```

## Production stack

1. Copy `.env.production.example` to `.env.production` and fill secrets.
2. Start services:

```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.production up --build -d
```

Stack includes: **Nginx** (port 80), **Gunicorn**, **Celery worker**, **Celery beat**, **PostgreSQL**, **Redis**.

### Health probes

| Endpoint | Use |
|----------|-----|
| `GET /api/v1/health/live` | Liveness |
| `GET /api/v1/health/ready` | Readiness |
| `GET /api/v1/health/` | Full health |
| `GET /api/v1/health/metrics` | Basic metrics |

### Backups

```bash
# Per-store backup
docker compose -f docker/docker-compose.prod.yml exec web python manage.py backup_store --store shop1

# Platform backup
docker compose -f docker/docker-compose.prod.yml exec web python manage.py backup_platform

# Restore
docker compose -f docker/docker-compose.prod.yml exec web python manage.py restore_store --store shop1 --archive /app/backups/... --yes
```

Nightly store backups run via Celery beat (`backup_active_stores`).

### Monitoring

- Set `SENTRY_DSN` in `.env.production` for error tracking.
- Logs: `docker compose -f docker/docker-compose.prod.yml logs -f web`
- Metrics: poll `/api/v1/health/metrics`

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):

- Postgres + Redis services
- Migration check
- `pytest` with coverage
- Docker image build on `main`

## Testing

```bash
pytest                          # all tests (uses config.settings.test)
pytest --cov=.                  # with coverage
make test-cov                   # via Makefile
```

Integration tests: `tests/integration/`  
E2E smoke tests: `tests/e2e/`
