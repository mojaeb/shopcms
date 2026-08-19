# راهنمای راه‌اندازی سرور

## پیش‌نیازها

- VPS با Ubuntu 22.04+ (حداقل 2GB RAM)
- دامنه با DNS مدیریت‌شده (A record به IP سرور)
- پورت 80 و 443 باز

---

## 1. آماده‌سازی سرور

```bash
# به‌روزرسانی سیستم
apt update && apt upgrade -y

# نصب Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER

# نصب Docker Compose Plugin (معمولاً با Docker نصب می‌شه)
docker compose version
```

---

## 2. نصب Nginx Proxy Manager

روی سرور یک پوشه جداگانه برای NPM بسازید:

```bash
mkdir -p /opt/nginx-proxy-manager && cd /opt/nginx-proxy-manager
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
      - "81:81"     # پنل مدیریت NPM
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt

volumes:
  data:
  letsencrypt:
```

```bash
docker compose up -d
```

پنل NPM: `http://YOUR_SERVER_IP:81`
- ایمیل پیش‌فرض: `admin@example.com`
- رمز پیش‌فرض: `changeme`

---

## 3. راه‌اندازی پروژه ShopCMS

```bash
mkdir -p /opt/shopcms && cd /opt/shopcms
git clone https://github.com/YOUR_USERNAME/shopcms.git .
```

فایل `.env.production` را بسازید:

```bash
cp .env.example .env.production
nano .env.production
```

مقادیر مهم:

```env
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=shop1.yourdomain.com,gohar.yourdomain.com,localhost
DATABASE_URL=postgres://shopcms:STRONG_PASSWORD@db:5432/shopcms
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
POSTGRES_PASSWORD=STRONG_PASSWORD
GHCR_OWNER=your-github-username
```

اجرا:

```bash
docker compose -f docker/docker-compose.vps.yml up -d
```

---

## 4. تنظیم Nginx Proxy Manager

در پنل NPM (`http://YOUR_IP:81`):

**Proxy Hosts** → **Add Proxy Host**:

| فیلد | مقدار |
|------|-------|
| Domain Names | `shop1.yourdomain.com` |
| Scheme | `http` |
| Forward Hostname / IP | `127.0.0.1` |
| Forward Port | `8000` |
| Block Common Exploits | ✓ |
| Websockets Support | ✓ |

تب **SSL**:
- SSL Certificate: Let's Encrypt
- Force SSL: ✓
- HTTP/2 Support: ✓

همین را برای هر دامنه‌ای که دارید تکرار کنید.

---

## 5. تنظیم GitHub Actions Secrets

در GitHub → Repository → Settings → Secrets → Actions:

| Secret | مقدار |
|--------|-------|
| `SERVER_HOST` | IP یا hostname سرور |
| `SERVER_USER` | نام کاربری SSH (مثلاً `root` یا `deploy`) |
| `SERVER_SSH_KEY` | محتوای کامل فایل private key (`~/.ssh/id_ed25519`) |
| `SERVER_PORT` | پورت SSH (پیش‌فرض ۲۲) |

ساخت SSH key برای deploy:

```bash
# روی کامپیوتر محلی
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/shopcms_deploy

# مقدار pub را به سرور اضافه کنید
ssh-copy-id -i ~/.ssh/shopcms_deploy.pub user@your-server

# مقدار private key را در GitHub secret بگذارید
cat ~/.ssh/shopcms_deploy
```

---

## 6. اولین deploy دستی

```bash
cd /opt/shopcms

# لاگین به GitHub Container Registry
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Pull و run
docker compose -f docker/docker-compose.vps.yml pull
docker compose -f docker/docker-compose.vps.yml up -d

# Migrate و seed
docker compose -f docker/docker-compose.vps.yml exec web python manage.py migrate
docker compose -f docker/docker-compose.vps.yml exec web python manage.py seed_store
docker compose -f docker/docker-compose.vps.yml exec web python manage.py seed_roles
docker compose -f docker/docker-compose.vps.yml exec web python manage.py seed_store_admin
# ... بقیه seeds
docker compose -f docker/docker-compose.vps.yml exec web python manage.py collectstatic --noinput
```

---

## 7. بعد از این — هر push به main

```
git add . && git commit -m "..." && git push origin main
```

GitHub Actions به‌صورت خودکار:
1. تست‌ها را اجرا می‌کند
2. Docker image را build و push می‌کند به `ghcr.io`
3. به سرور SSH می‌زند
4. `docker compose up -d --pull always` را اجرا می‌کند
5. migrate را اجرا می‌کند

**زمان تقریبی deploy: ۳–۵ دقیقه**
