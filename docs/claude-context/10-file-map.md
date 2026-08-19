# 10 — File map (read these first)

## Bootstrap

| File | Why |
|------|-----|
| `manage.py` | DJANGO_SETTINGS_MODULE default |
| `config/settings/base.py` | apps, middleware, templates, cache, celery beat, unfold, auth |
| `config/settings/development.py` | LocMem, fixed OTP, `.local` hosts |
| `config/urls.py` | mounts |
| `config/celery.py` | Celery app |

## Tenancy & themes

| File | Why |
|------|-----|
| `tenants/middleware.py` | host → store |
| `tenants/models.py` | Store, Domain, Theme, settings |
| `tenants/urls.py` | all storefront + manage routes |
| `tenants/views/storefront.py` | HTML views → ThemeEngine |
| `tenants/views/store_admin_ui.py` | /manage/ |
| `tenants/theme/pages.py` | page key → filename |
| `tenants/theme/engine.py` | render_page |
| `tenants/theme/loader.py` | Django template loader |
| `tenants/services/theme.py` | ThemeResolver fallback |
| `tenants/templatetags/theme_tags.py` | theme_include, theme_asset |
| `tenants/templatetags/money_tags.py` | money display |
| `tenants/context_processors.py` | store/theme in every template |
| `tenants/management/commands/seed_store.py` | sample shop1 + themes |

## API & auth

| File | Why |
|------|-----|
| `core/api/__init__.py` | router mount table |
| `accounts/models.py` | User phone |
| `accounts/api/auth.py` | OTP/JWT endpoints |
| `accounts/services/otp.py` | OTP rules |
| `dashboard/api/store_admin.py` | store admin API |
| `dashboard/api/super_admin.py` | super admin API |
| `dashboard/authentication_store.py` | permission auth |

## Commerce

| File | Why |
|------|-----|
| `products/models.py` | catalog |
| `carts/api/cart.py` | cart HTTP |
| `carts/services/cart.py` | cart logic + serialize |
| `addresses/api/addresses.py` | |
| `shipping/api/public.py` | calculate quotes |
| `taxes/services/tax.py` | |
| `payments/api/payments.py` | create + callback |
| `payments/services/payment.py` | |
| `orders/services/order.py` | create_from_payment |
| `orders/models.py` | snapshots |

## Storefront assets

| File | Why |
|------|-----|
| `static/js/cart.js` | add-to-cart + cart page |
| `static/js/checkout.js` | checkout orchestration |
| `static/js/auth.js` | OTP UI |
| `static/js/money.js` | toman / Persian digits |
| `themes/default/base.html` | fallback chrome |
| `themes/default/cart.html` | `#cart-page` contract |
| `themes/default/checkout.html` | `#checkout-page` IDs |
| `themes/pulse/src/main.js` | Vite entry |
| `themes/pulse/vite.config.js` | outDir static/themes/pulse |
| `templates/store_admin/base.html` | manage UI chrome |

## Docs already in repo

| File | Why |
|------|-----|
| `docs/REQUIREMENTS_AND_PHASES.md` | original Persian spec |
| `docs/LOCAL_SETUP.md` | Windows setup |
| `docs/AUTH.md` | login matrix |
| `docs/DEPLOYMENT.md` | docker/prod |
| `PRODUCT.md` / `DESIGN.md` | minimal theme design lane |
| `design-system/nextshop/DESIGN.md` | nextshop tokens |
| `themes/pulse/README.md` / `themes/gohar/README.md` | Vite themes |

## Plugins

| File | Why |
|------|-----|
| `plugins/loader.py` | URL + API registration |
| `plugins/builtin/__init__.py` | store-type + feature plugins |
| `plugins/base.py` | BasePlugin |

When fixing a bug: start at the **service**, then API, then JS/template IDs — not the other way around unless it is purely visual.
