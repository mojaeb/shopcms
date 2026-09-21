# راهنمای اجرای ShopCMS روی سرور

این سند برای بالا آوردن پروژه روی VPS واقعی (Ubuntu) نوشته شده است.
برای اجرای لوکال، فایل [LOCAL_SETUP.md](./LOCAL_SETUP.md) را ببینید.

مسیر پروژه روی سرور پیشنهادی:

```
/opt/shopcms
```

ریموت گیت: `https://github.com/mojaeb/shopcms.git`

---

## کدام روش را انتخاب کنید؟

| روش | فایل Compose | مناسب برای | پورت روی سرور |
|------|----------------|-------------|----------------|
| **۱ — پیشنهادی** | `docker/docker-compose.vps.yml` | دامنه + SSL با Nginx Proxy Manager | اپ پورت host نمی‌گیرد؛ NPM روی `80` و `443` |
| **۲ — استک مستقل** | `docker/docker-compose.prod.yml` | سرور بدون NPM؛ Nginx داخل خود پروژه | Nginx اپ روی `80` |

هر دو روش این سرویس‌ها را بالا می‌آورند: **Gunicorn (Django)**، **Celery worker**، **Celery beat**، **PostgreSQL 16**، **Redis 7**.

> روی یک سرور هر دو را با هم اجرا نکنید. هر دو به پورت `80` یا شبکهٔ `proxy` نیاز دارند و با هم تداخل می‌کنند.

---

## پیش‌نیازها

| مورد | حداقل | توضیح |
|------|--------|--------|
| سیستم‌عامل | Ubuntu 22.04+ | Debian هم قابل استفاده است |
| RAM | 2 GB | 4 GB بهتر است |
| دیسک | 20 GB | media و بکاپ فضا می‌گیرند |
| Docker | Engine + Compose plugin | نصب در مرحلهٔ ۱ |
| دامنه | A record به IP سرور | مثلاً `lonamarket.com` و `www` |
| پورت باز | `22`، `80`، `443` | فایروال |

---

## ۱. آماده‌سازی سرور

با کاربر `root` یا کاربری با sudo:

```bash
apt update && apt upgrade -y
apt install -y git curl ufw

# فایروال
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
# اگر Nginx Proxy Manager می‌خواهید، پنل روی 81 است:
ufw allow 81/tcp
ufw --force enable

# نصب Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker "$USER"
```

از سرور خارج شوید و دوباره SSH بزنید تا گروه `docker` اعمال شود. سپس:

```bash
docker compose version
```

شبکهٔ مشترک پروکسی را یک‌بار بسازید (برای هر دو روش لازم است):

```bash
docker network create proxy
```

اگر پیام `already exists` دیدید، مشکلی نیست.

---

## ۲. کلون پروژه و فایل محیط

```bash
mkdir -p /opt/shopcms
cd /opt/shopcms
git clone https://github.com/mojaeb/shopcms.git .
```

فایل محیط production را بسازید:

```bash
cp .env.production.example .env.production
nano .env.production
```

حداقل این مقادیر را پر کنید. **رمزها را واقعی و یکتا بگذارید؛ نمونهٔ زیر را کپی نکنید.**

```env
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=یک-رشته-تصادفی-طولانی
DEBUG=False

ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

SHOPCMS_IMAGE=shopcms:latest
POSTGRES_IMAGE=postgres:16-alpine
REDIS_IMAGE=redis:7-alpine

DATABASE_URL=postgres://shopcms:STRONG_PASSWORD@db:5432/shopcms
POSTGRES_PASSWORD=STRONG_PASSWORD

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
RATE_LIMIT_ENABLED=True

STATIC_URL=/static/
MEDIA_URL=/media/

LOG_LEVEL=INFO
SENTRY_DSN=
PLATFORM_NAME=ShopCMS
DEFAULT_STORE_SLUG=shop1

OTP_USE_FIXED_CODE=False

BACKUP_RETENTION_DAYS=30
AUDIT_LOG_RETENTION_DAYS=90

GUNICORN_WORKERS=4
GUNICORN_THREADS=2
```

نکات مهم:

- `POSTGRES_PASSWORD` باید با رمز داخل `DATABASE_URL` یکی باشد.
- `ALLOWED_HOSTS` همهٔ دامنه‌های فروشگاه (با و بدون `www`) را شامل شود.
- `CSRF_TRUSTED_ORIGINS` باید با **https** نوشته شود (بعد از فعال شدن SSL).
- `OTP_USE_FIXED_CODE` در production حتماً `False` باشد.
- ساخت `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

اگر چند فروشگاه / چند دامنه دارید، همه را با کاما جدا کنید:

```env
ALLOWED_HOSTS=lonamarket.com,www.lonamarket.com,atrangiz.ir,www.atrangiz.ir
CSRF_TRUSTED_ORIGINS=https://lonamarket.com,https://www.lonamarket.com,https://atrangiz.ir,https://www.atrangiz.ir
```

---

## ۳. روش ۱ — پیشنهادی: VPS + Nginx Proxy Manager

این همان مسیری است که GitHub Actions (`cd.yml`) روی سرور اجرا می‌کند.

### ۳.۱ نصب Nginx Proxy Manager

پوشهٔ جدا از پروژه:

```bash
mkdir -p /opt/nginx-proxy-manager
cd /opt/nginx-proxy-manager
```

فایل `docker-compose.yml`:

```yaml
services:
  npm:
    image: jc21/nginx-proxy-manager:latest
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "81:81"
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt
    networks:
      - proxy

networks:
  proxy:
    name: proxy
    external: true
```

```bash
docker compose up -d
```

پنل: `http://IP-سرور:81`

- ایمیل پیش‌فرض: `admin@example.com`
- رمز پیش‌فرض: `changeme`

بعد از ورود، ایمیل و رمز را عوض کنید. پورت `81` را بعداً در فایروال محدود کنید.

### ۳.۲ بیلد ایمیج اپ

از ریشهٔ پروژه:

```bash
cd /opt/shopcms
```

اگر Docker Hub فیلتر است و `docker pull` با `denied` می‌ایستد، اول ایمیج‌های پایه را از آینه بگیرید:

```bash
docker pull mirror.gcr.io/library/python:3.12-slim
docker tag  mirror.gcr.io/library/python:3.12-slim python:3.12-slim
docker pull mirror.gcr.io/library/redis:7-alpine
docker tag  mirror.gcr.io/library/redis:7-alpine redis:7-alpine
docker pull mirror.gcr.io/library/postgres:16-alpine
docker tag  mirror.gcr.io/library/postgres:16-alpine postgres:16-alpine
```

سپس ایمیج اپ را بسازید و سرویس‌ها را بالا بیاورید:

```bash
docker build -t shopcms:latest -f docker/Dockerfile .

docker compose -f docker/docker-compose.vps.yml --env-file .env.production up -d --pull never
```

`--pull never` جلوی تلاش Compose برای گرفتن ایمیج از GHCR را می‌گیرد (تا وقتی هنوز لاگین registry ندارید).

وضعیت:

```bash
docker compose -f docker/docker-compose.vps.yml --env-file .env.production ps
```

سرویس‌های سالم: `web`، `db`، `redis`، `celery`، `celery-beat`. کانتینر وب نام `shopcms-web` دارد.

### ۳.۳ تنظیم دامنه در NPM

در پنل NPM → **Proxy Hosts** → **Add Proxy Host**:

| فیلد | مقدار |
|------|--------|
| Domain Names | `yourdomain.com` و `www.yourdomain.com` |
| Scheme | `http` |
| Forward Hostname / IP | `shopcms-nginx` |
| Forward Port | `80` |
| Block Common Exploits | روشن |
| Websockets Support | روشن |

> به `shopcms-web:8000` نزنید. آنجا Gunicorn است و فایل‌های `/media/` (عکس کالا) را سرو نمی‌کند. Nginx داخلی (`shopcms-nginx`) هم `/media/` و `/static/` را می‌دهد و هم بقیه را به Django می‌فرستد.

کانتینر NPM باید روی شبکهٔ `proxy` باشد تا نام `shopcms-nginx` را ببیند. اگر NPM از قبل روی سرور بوده و روی این شبکه نیست:

```bash
docker network connect proxy nginx-proxy-manager
```

شبکهٔ فعلی را با این دستور چک کنید:

```bash
docker inspect nginx-proxy-manager --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
docker inspect shopcms-nginx --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
```

اگر نام شبکهٔ NPM چیز دیگری بود (مثلاً `npm_default`)، nginx را به همان شبکه وصل کنید:

```bash
docker network connect npm_default shopcms-nginx
```

تب **SSL**:

- SSL Certificate: Request a new SSL Certificate (Let's Encrypt)
- Force SSL: روشن
- HTTP/2 Support: روشن
- ایمیل معتبر برای Let's Encrypt

برای هر دامنهٔ فروشگاه همین Proxy Host را تکرار کنید.

در تب **Advanced** این قطعه را بگذارید تا پروتکل HTTPS درست به Django برسد و فایل‌های آپلود (`/media/`) از volume سرو شوند. اگر media را از NPM سرو نمی‌کنید، حداقل هدرها را نگه دارید:

```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
client_max_body_size 20M;
```

Static را WhiteNoise از خود Django سرو می‌کند. Media در این روش از Gunicorn سرو نمی‌شود (`DEBUG=False`). برای عکس‌های آپلودشده یکی از این دو کار را بکنید:

- روش ۲ (Nginx داخلی پروژه) را استفاده کنید، یا
- volume مدیا را به‌صورت bind-mount به مسیر ثابت روی دیسک ببرید و در NPM یک location برای `/media/` تعریف کنید.

ساده‌ترین راه برای media روی همین استک: در `docker-compose.vps.yml` به‌جای named volume از bind استفاده کنید، مثلاً `/opt/shopcms/media:/app/media`، بعد در NPM Custom Nginx Config:

```nginx
location /media/ {
    alias /opt/shopcms/media/;
    expires 7d;
}
```

این `alias` فقط وقتی کار می‌کند که همان مسیر روی **هاست** به کانتینر NPM هم mount شده باشد. اگر این بخش را فعلاً نمی‌خواهید پیچیده کنید، از روش ۲ استفاده کنید؛ آنجا Nginx پروژه `/media/` و `/static/` را خودش سرو می‌کند.

### ۳.۴ مایگریشن و دادهٔ اولیه

Compose هنگام استارت `web` خودش `migrate` را اجرا می‌کند. برای اطمینان:

```bash
cd /opt/shopcms

docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web \
  python manage.py migrate --noinput
```

اگر فروشگاه خالی است (اولین نصب)، seed بزنید:

```bash
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py seed_store
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py seed_roles
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py seed_store_admin
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py seed_plugins
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py seed_cms
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py seed_products
```

سوپرادمین Django Admin (شماره موبایل به‌جای username):

```bash
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec -it web \
  python manage.py createsuperuser
```

دامنه‌های Tenant را در پنل Store Admin (`/manage/settings/`) یا Django Admin روی همان دامنه‌ای که به سرور اشاره می‌کند تنظیم کنید. بدون این کار ممکن است صفحهٔ «فروشگاه یافت نشد» ببینید.

---

## ۴. روش ۲ — استک مستقل با Nginx داخلی

وقتی Nginx Proxy Manager نمی‌خواهید و اپ باید مستقیم روی پورت `80` گوش بدهد.

```bash
cd /opt/shopcms
docker network create proxy   # اگر از قبل نیست

docker compose -f docker/docker-compose.prod.yml --env-file .env.production up --build -d
```

سرویس‌ها: **nginx:80**، **web (Gunicorn:8000)**، **celery**، **celery-beat**، **db**، **redis**.

Nginx داخل پروژه `/static/` و `/media/` را از volume سرو می‌کند و بقیهٔ درخواست‌ها را به Gunicorn می‌فرستد.

مایگریشن هنگام استارت `web` اجرا می‌شود. seed و superuser مثل روش ۱ است؛ فقط فایل compose را عوض کنید:

```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.production exec web python manage.py migrate --noinput
docker compose -f docker/docker-compose.prod.yml --env-file .env.production exec web python manage.py seed_store
# ... بقیهٔ seedها
```

SSL را در این روش باید جدا بگذارید (Cloudflare Flexible/Full، یا Certbot روی هاست، یا یک reverse proxy جلوتر). تا وقتی HTTPS ندارید موقتاً:

```env
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
CSRF_TRUSTED_ORIGINS=http://yourdomain.com,http://www.yourdomain.com
```

بعد از فعال شدن HTTPS این سه مقدار را به حالت امن برگردانید.

---

## ۵. آدرس‌ها بعد از اجرا

به‌جای `yourdomain.com` دامنهٔ واقعی را بگذارید.

| آدرس | توضیح |
|------|--------|
| `https://yourdomain.com/` | فروشگاه (storefront) |
| `https://yourdomain.com/manage/` | پنل Store Admin |
| `https://yourdomain.com/login/` | ورود مشتری / ادمین |
| `https://yourdomain.com/admin/` | Django Admin |
| `https://yourdomain.com/api/v1/docs` | Swagger |
| `https://yourdomain.com/api/v1/health/` | سلامت کامل |
| `https://yourdomain.com/api/v1/health/live` | Liveness |
| `https://yourdomain.com/api/v1/health/ready` | Readiness |
| `https://yourdomain.com/api/v1/health/metrics` | متریک ساده |

ادمین نمونه بعد از `seed_store_admin`: شماره **`09120000000`**. در production کد OTP ثابت خاموش است؛ OTP واقعی به کانال پیامک/تنظیمات شما می‌رود.

---

## ۶. به‌روزرسانی بعدی (دستی)

```bash
cd /opt/shopcms
git pull origin main

docker build -t shopcms:latest -f docker/Dockerfile .
docker compose -f docker/docker-compose.vps.yml --env-file .env.production up -d --no-build --pull never

docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web \
  python manage.py migrate --noinput
```

برای روش ۲، همان `git pull` و بعد:

```bash
docker compose -f docker/docker-compose.prod.yml --env-file .env.production up --build -d
```

تم‌هایی که Vite دارند (`themes/nextshop`، `themes/pulse`، `themes/gohar`) قبل از بیلد ایمیج باید build شده باشند. در CI این کار خودکار است. اگر دستی بیلد می‌کنید و CSS/JS تم تازه است:

```bash
for theme in nextshop pulse gohar; do
  if [ -f "themes/$theme/package.json" ]; then
    (cd "themes/$theme" && npm ci && npm run build)
  fi
done
```

سپس دوباره `docker build`.

---

## ۷. Deploy خودکار با GitHub Actions

Workflow: `.github/workflows/cd.yml`

با هر push به `main` / `master`:

1. تست اجرا می‌شود
2. ایمیج Docker به `ghcr.io/mojaeb/shopcms` پوش می‌شود
3. با SSH به سرور وصل می‌شود، ایمیج را pull می‌کند و `docker-compose.vps.yml` را بالا می‌آورد
4. `migrate` اجرا می‌شود

در GitHub → Settings → Secrets and variables → Actions این secretها را بگذارید:

| Secret | مقدار |
|--------|--------|
| `SERVER_HOST` | IP یا hostname سرور |
| `SERVER_USER` | کاربر SSH (مثلاً `root`) |
| `SERVER_SSH_KEY` | کل محتوای private key |
| `SERVER_PORT` | پورت SSH (پیش‌فرض `22`) |

ساخت کلید deploy:

```bash
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/shopcms_deploy
ssh-copy-id -i ~/.ssh/shopcms_deploy.pub USER@SERVER_IP
```

محتوای `~/.ssh/shopcms_deploy` را در secret `SERVER_SSH_KEY` بگذارید.

روی سرور، برای pull از GHCR:

```bash
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

مسیر روی سرور در workflow ثابت است: `/opt/shopcms`. پروژه را همان‌جا کلون کنید.

---

## ۸. لاگ، سلامت، شل

روش ۱:

```bash
cd /opt/shopcms
COMPOSE="docker compose -f docker/docker-compose.vps.yml --env-file .env.production"

$COMPOSE logs -f web
$COMPOSE logs -f celery
$COMPOSE ps
$COMPOSE exec web python manage.py shell
```

روش ۲ همان است با `docker/docker-compose.prod.yml`.

Health از داخل سرور:

```bash
curl -sS http://127.0.0.1:8000/api/v1/health/live
```

اگر از NPM استفاده می‌کنید پورت `8000` روی host باز نیست؛ از داخل کانتینر چک کنید:

```bash
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web \
  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live').read())"
```

---

## ۹. پشتیبان‌گیری و بازیابی

```bash
cd /opt/shopcms
COMPOSE="docker compose -f docker/docker-compose.vps.yml --env-file .env.production"

# بکاپ یک فروشگاه
$COMPOSE exec web python manage.py backup_store --store shop1

# بکاپ کل پلتفرم
$COMPOSE exec web python manage.py backup_platform

# بازیابی فروشگاه
$COMPOSE exec web python manage.py restore_store --store shop1 --archive /app/backups/ARCHIVE.tar.gz --yes
```

فایل‌های بکاپ داخل volume `backup_volume` هستند (مسیر داخل کانتینر: `/app/backups`). بکاپ شبانهٔ فروشگاه‌های فعال با Celery beat (`backup_active_stores`) اجرا می‌شود. نگهداری: `BACKUP_RETENTION_DAYS` در `.env.production`.

کپی بکاپ روی هاست:

```bash
docker compose -f docker/docker-compose.vps.yml --env-file .env.production cp web:/app/backups ./backups-copy
```

---

## ۱۰. مشکلات رایج

### `network proxy declared as external, but could not be found`

```bash
docker network create proxy
```

### `bind: address already in use` روی پورت 80

یا NPM بالاست یا Nginx داخلی. فقط یکی را روی `80` نگه دارید.

```bash
ss -tlnp | grep -E ':80|:443|:81'
```

### Docker Hub: `denied` / timeout

ایمیج‌های `python`، `postgres`، `redis` را از آینه بکشید و tag کنید (بخش ۳.۲). بعد با `--pull never` بالا بیاورید.

### `DisallowedHost` یا 400

دامنه را به `ALLOWED_HOSTS` اضافه کنید و کانتینر `web` را restart کنید:

```bash
docker compose -f docker/docker-compose.vps.yml --env-file .env.production up -d web --force-recreate
```

### خطای CSRF هنگام لاگین / پنل

`CSRF_TRUSTED_ORIGINS` باید دقیقاً origin مرورگر باشد (`https://yourdomain.com` بدون اسلش آخر). اگر NPM هدر `X-Forwarded-Proto` را نفرستد، Django درخواست را HTTP می‌بیند.

### ریدایرکت حلقه‌ای HTTPS

`SECURE_SSL_REDIRECT=True` است ولی پروکسی HTTPS را نشان نمی‌دهد. در NPM گزینهٔ Force SSL و هدر `X-Forwarded-Proto` را چک کنید. تنظیم Django از قبل `SECURE_PROXY_SSL_HEADER` دارد.

### «فروشگاه یافت نشد»

- `seed_store` اجرا شده باشد
- دامنه در Tenant به همان Host تنظیم شده باشد
- `DEFAULT_STORE_SLUG` درست باشد

### OTP کار نمی‌کند

در production کد ثابت خاموش است. تا وقتی درگاه پیامک تنظیم نشده، ورود ادمین از `/admin/` با سوپرادمین ممکن است. `OTP_USE_FIXED_CODE=True` را روی سرور واقعی نگذارید.

### دیتابیس خالی بعد از `down -v`

فلگ `-v` volumeها را پاک می‌کند (Postgres، media، بکاپ). برای توقف عادی فقط:

```bash
docker compose -f docker/docker-compose.vps.yml --env-file .env.production down
```

---

## ۱۱. خلاصهٔ دستورات (کپی سریع — روش ۱)

```bash
# یک‌بار روی سرور
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
docker network create proxy

mkdir -p /opt/shopcms && cd /opt/shopcms
git clone https://github.com/mojaeb/shopcms.git .
cp .env.production.example .env.production
nano .env.production

docker build -t shopcms:latest -f docker/Dockerfile .
docker compose -f docker/docker-compose.vps.yml --env-file .env.production up -d --pull never

docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py migrate --noinput
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py seed_store
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py seed_roles
docker compose -f docker/docker-compose.vps.yml --env-file .env.production exec web python manage.py seed_store_admin
```

بعد Nginx Proxy Manager را روی شبکهٔ `proxy` بالا بیاورید و دامنه را به `shopcms-web:8000` بفرستید.

سپس باز کنید:

- فروشگاه: **https://yourdomain.com/**
- پنل: **https://yourdomain.com/manage/**
- Django Admin: **https://yourdomain.com/admin/**

---

جزئیات staging، health probe و تست در [DEPLOYMENT.md](./DEPLOYMENT.md) است.
راهنمای قدیمی‌تر همین موضوع: [deploy/SERVER_SETUP.md](./deploy/SERVER_SETUP.md).
