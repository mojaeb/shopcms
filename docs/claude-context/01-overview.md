# 01 — Overview

## Product

**ShopCMS** is a multi-tenant commerce **platform** (not one shop). Super-admins create stores, assign domains/themes/admins. Each storefront is mostly theme + `StoreSetting` JSON.

**Market:** Iranian / Persian RTL shops. Voice: direct Persian, short, no hype.

**Canonical intent docs in repo (not duplicated here):**
- `docs/REQUIREMENTS_AND_PHASES.md` — original product spec (Persian)
- `PRODUCT.md` / `DESIGN.md` — storefront design lane (minimal theme as fashion/decor reference)
- `docs/AUTH.md`, `docs/LOCAL_SETUP.md`, `docs/DEPLOYMENT.md`

## Key capabilities

- Multi-store tenancy by **domain** (`Domain` → `Store`)
- Store types: physical+shipping, digital download, subscription (booking/appointment/rental/POD **stubbed**)
- Theme system with fallback to `themes/default/`
- Catalog: simple / variable / digital / subscription products
- AJAX cart, coupons, gift cards
- Checkout → Iranian gateways (Zarinpal implemented; IdPay/Mellat/Pasargad in enum)
- Shipping: post / tipax / peyk / free / api; modes fixed / distance / weight / distance+weight
- Customer area: orders, invoices, wishlist, addresses, comments, downloads, subscriptions
- Store admin HTML at `/manage/` + store-admin APIs
- Super-admin APIs + Django Unfold at `/admin/`
- CMS (pages, menus, banners, sliders, widgets, shortcodes), blog, comments
- Files/media, notifications, reports, backups, plugins, rate limits, audit logs

## Tech stack

| Layer | Choice |
|--------|--------|
| Language | Python 3.10+ |
| Framework | Django ≥5.0,<5.2 |
| API | **django-ninja** (not DRF). OpenAPI: `/api/v1/docs` |
| Admin | django-unfold + RTL/Yekan CSS |
| Config | django-environ (`.env`) |
| DB | SQLite local default; PostgreSQL via `DATABASE_URL` |
| Cache | LocMem in development/test; Redis (`django-redis`) in prod |
| Tasks | Celery + Redis; Beat schedule in settings |
| Static | WhiteNoise CompressedManifestStaticFilesStorage |
| Auth tokens | PyJWT; OTP via pyotp (2FA TOTP) |
| Images | Pillow |
| Storefront | Django templates + shared `static/js/*` |
| Vite | **Only** `themes/pulse` and `themes/gohar` (Vite 7 + Tailwind v4) |
| Payments | Provider registry; Zarinpal implemented |
| Tests | pytest + pytest-django + factory-boy |
| Monitoring | Optional Sentry in production |

Default settings module (`manage.py`): `config.settings.development`.

## Django apps

| App | Purpose |
|-----|---------|
| `core` | Health, backup, audit, security middleware, Celery tasks, `TimeStampedModel` |
| `tenants` | Store, Domain, Theme, StoreSetting, plugins models; TenantMiddleware; theme engine; storefront + `/manage/` views |
| `accounts` | Phone `User`, Role/Permission, StoreMembership, OTP, 2FA, devices |
| `dashboard` | Super-admin & store-admin API orchestration (no models) |
| `cms` | Pages, menus, banners, sliders, widgets, blocks, shortcodes, SEO mixin |
| `products` | Categories, brands, attributes, products, variants, images, inventory |
| `carts` | Cart/items, coupons, gift cards |
| `addresses` | Iranian customer addresses |
| `shipping` | Zones, methods, price tables, calculator |
| `payments` | PaymentTransaction + gateway providers |
| `orders` | Order lifecycle, snapshots, shipment, invoice |
| `taxes` | Tax rules + cart tax |
| `wishlists` | Wishlist items |
| `comments` | Product comments + likes |
| `blog` | Categories/tags/posts/comments |
| `files` | MediaFile + thumbnails |
| `notifications` | Channels + logs |
| `plugins` | Registry/loader; built-in store-type plugins |
| `digital` | Digital assets + download licenses |
| `subscriptions` | Plans, customer subscriptions, renewals |
| `reports` | Store reporting APIs (service-only) |

Typical layering: `models.py` → `services/` → `api/` → `repositories/` → `management/commands/` → `tests/`.

## Top-level directories

| Path | Role |
|------|------|
| `config/` | Django project: settings, urls, wsgi/asgi, celery |
| `themes/` | Per-theme HTML (+ Vite src for pulse/gohar) |
| `static/` | Shared JS/CSS + built theme assets `static/themes/{name}/` |
| `templates/` | Non-theme: Unfold helpers, `store_admin/` HTML |
| `docker/` | Dockerfile, compose, nginx, gunicorn, seed-data |
| `docs/` | Setup, deploy, auth, this Claude pack |
| `requirements/` | `base.txt`, `development.txt`, `production.txt` |
| `tests/` | Cross-app integration + e2e smoke |
| `media/`, `backups/`, `logs/` | Runtime data |

## Sample local identities

| What | Value |
|------|--------|
| Default store slug | `shop1` (“فروشگاه نمونه”) |
| Default theme after seed | `round` (fallback `default`) |
| Domains | `localhost` (primary), `127.0.0.1`, `shop1.local` |
| Store admin | phone `09120000000`, OTP `12345` |
| Gohar store | slug `gohar`, hosts `gohar.local` / `gohar.localhost` (after `seed_gohar`) |
| Currency | IRR (toman display) |
| Tax on sample store | enabled, 9% |
