# 02 — Architecture

## Settings

```
config/settings/
  base.py          # shared
  development.py   # DEBUG, LocMem, fixed OTP, debug toolbar, ALLOWED_HOSTS includes .local
  staging.py
  production.py    # HTTPS cookies/HSTS, Sentry
  test.py          # pytest: LocMem, eager Celery, MD5 hasher, fixed OTP
```

Env: `environ.Env.read_env(BASE_DIR / ".env")` in `base.py`.

There is **no per-shop Python settings module**. Shop config is DB: `Store`, `StoreSetting` (JSON key-values by group), theme FK.

### Important env vars

| Var | Meaning |
|-----|---------|
| `DJANGO_SETTINGS_MODULE` | settings module |
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Django core |
| `DATABASE_URL` | sqlite or postgres |
| `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | cache/tasks |
| `DEFAULT_STORE_SLUG` | fallback slug (`shop1`) |
| `OTP_USE_FIXED_CODE`, `OTP_FIXED_CODE` | dev OTP (`12345`) |
| `STATIC_URL`, `MEDIA_URL` | assets |
| `CSRF_TRUSTED_ORIGINS`, `SECURE_*` | prod security |
| `SENTRY_DSN` | optional |
| `BACKUP_RETENTION_DAYS`, `AUDIT_LOG_RETENTION_DAYS` | retention |
| `RATE_LIMIT_*`, `CACHE_TTL_*` | limits / TTLs |
| `CORS_ALLOWED_ORIGINS` | noted for future SPA |

i18n in base: `LANGUAGE_CODE = "fa-ir"`, `TIME_ZONE = "Asia/Tehran"`.

`AUTH_USER_MODEL = "accounts.User"`.

## Middleware order (base)

1. SecurityMiddleware
2. WhiteNoise
3. `core.middleware.security_headers.SecurityHeadersMiddleware`
4. `core.middleware.rate_limit.APIRateLimitMiddleware`
5. Session / Common / CSRF / Auth
6. **`tenants.middleware.TenantMiddleware`**
7. Messages / XFrameOptions

## Templates

- `DIRS`: `[BASE_DIR / "templates", BASE_DIR]` so `themes/` is reachable
- Loaders: **ThemeLoader first**, then filesystem, then app_directories
- Context processors: store, theme, cms (+ Django defaults)
- Builtins always loaded: `tenants.templatetags.theme_tags`, `tenants.templatetags.money_tags`

## URL routing

Root: `config/urls.py`

| Mount | What |
|-------|------|
| `/admin/` | Unfold admin |
| `/api/v1/` | Ninja API + plugin routers |
| `/download/<token>/` | Digital file download |
| `""` → `tenants.urls` | Storefront + `/manage/` |
| Plugin URLconfs | `plugins.loader.get_plugin_urlpatterns()` |

`handler404 = tenants.views.storefront.storefront_404` (themed).

DEBUG also serves media/static and debug toolbar at `/__debug__/`.

### Storefront / manage (`tenants/urls.py`)

SEO: `robots.txt`, `sitemap.xml`, `google{token}.html`.

**Store admin HTML (`/manage/`):** dashboard, products CRUD, files, orders, settings, pages, blog, comments, shortcodes. Templates live in `templates/store_admin/` (NOT themed).

**Customer storefront:**

| Path | View name / page key |
|------|----------------------|
| `/` | home |
| `/products/`, `/products/<slug>/` | category |
| `/product/<slug>/` | product |
| `/search/` | search |
| `/cart/` | cart |
| `/checkout/` | checkout |
| `/order/success/` | order_success |
| `/dashboard/` | dashboard |
| `/profile/`, `/profile/edit/` | profile |
| `/wishlist/` | wishlist |
| `/orders/`, `/orders/<id>/` | orders |
| `/invoices/` | invoices |
| `/comments/` | comments |
| `/addresses/` | addresses |
| `/blog/`, `/blog/<slug>/` | blog |
| `/login/`, `/register/` | auth |
| `/downloads/` | downloads |
| `/subscriptions/` | subscriptions |
| `/page/<slug>/` | CMS page |

Legacy `/category/` redirects to `/products/`.

## Multi-tenancy

**Model:** shared DB, **row-level** tenancy via `store` FK (not schema-per-tenant).

**Resolution:** `tenants.middleware.TenantMiddleware`

1. Skip exempt: `/admin/`, `/api/v1/health/`, `/api/v1/super-admin/`, `/static/`, `/media/`, `/__debug__/`
2. Host → `Domain` → `Store` via `StoreService.resolve_by_host`
3. Optional redirect to primary domain
4. Sets `request.store`, `request.theme_slug`; thread-local store context
5. Inactive store → 404; unknown host → 404 (DEBUG: `request.store = None`, theme `default`)

Thread-local: `tenants.context.get_current_store()` / `activate` / `clear_current_store`.

### Store fields

name, slug, `store_type`, theme / default_theme, currency (default `IRR`), timezone, language (`fa`), status, tax_enabled, tax_percent.

`effective_theme` = `theme or default_theme`.  
`effective_theme_slug` = theme.directory or `"default"`.

### StoreSetting

`(store, group, key)` → JSON value. Groups include payment, shipping, theme, seo, …

### Domain

unique host, is_primary, ssl_enabled, redirect_to_primary, is_active. Host stored lowercased.

## Plugin system

- Platform `Plugin` + per-store `StorePlugin` (enable + settings JSON)
- Loader: `plugins/loader.py` — can register API routers and URL patterns
- Built-ins in `plugins/builtin/__init__.py`

**Store-type plugins:** `physical`, `digital_download`, `subscription`, `booking`, `appointment`, `rental`, `print_on_demand`  
Booking/appointment have stub HTML pages; rental/POD are stubs.

**Feature plugins:** blog, comments, wishlist, coupon, tax, shipping, payment, inventory.

## Cache invalidation (signals)

Primarily cache bust on save of Store/Domain/StoreSetting, product graph + inventory, CMS/blog content, Order (reports).

## Dual surface

| Surface | Auth | Templates |
|---------|------|-----------|
| Storefront HTML | Django session + JWT in sessionStorage for API calls from JS | `themes/` |
| Store admin HTML `/manage/` | Django session + store staff check | `templates/store_admin/` |
| Public + customer API | JWT Bearer and/or session | JSON |
| Store-admin API `/api/v1/store-admin/*` | JWT + store permission | JSON |
| Super-admin API `/api/v1/super-admin/*` | JWT + `is_superuser` | JSON |
| Django admin `/admin/` | phone + password, staff/superuser | Unfold |
