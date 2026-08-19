# START HERE — ShopCMS (for Claude)

You are working on **ShopCMS**: a **Persian-first, RTL, multi-tenant commerce platform** built with **Django 5 + django-ninja**. Super-admins create stores; each storefront is mostly “pick a theme + settings.” It is **not** a single Shopify clone — it is a **platform**.

## Mental model

```
Host → TenantMiddleware → Store (+ theme)
     ├─ HTML storefront: ThemeEngine → themes/{dir} with fallback to themes/default
     ├─ Shared JS: static/js/cart.js, checkout.js, auth.js, …
     ├─ /manage/ : store-staff HTML UI (Django session)
     ├─ /api/v1/ : Django Ninja (public + store-admin + super-admin)
     └─ /admin/  : Django Unfold (platform staff, phone + password)

Cart API → Checkout page → POST /api/v1/payments/create
         → Gateway (Zarinpal) → callback → OrderService.create_from_payment
```

## Non-negotiables

1. **Always scope by current store.** Almost every model has `store` FK. Never leak cross-tenant data.
2. **Persian RTL.** `LANGUAGE_CODE=fa-ir`, `TIME_ZONE=Asia/Tehran`, `dir=rtl`, IRANYekan. UI copy is short Persian.
3. **Money is integer IRR/toman** (`decimal_places=0`). Display with `{% money amount %}` or `window.ShopMoney`. Never invent `$` or cents.
4. **Add-to-cart requires login.** `POST /api/v1/cart/add` returns 401 if anonymous. Guest cart exists for session but add is gated.
5. **Business logic lives in `services/`**, not fat views. APIs are thin Ninja routers.
6. **Themes override only what they need.** Missing template → `themes/default/`. Shared behavior is in `static/js/*`, not duplicated per theme.
7. **Do not invent DRF.** API is **django-ninja**, mounted at `/api/v1/`, docs at `/api/v1/docs`.
8. **Auth:** storefront OTP (phone) + JWT in `sessionStorage` + Django session. `/admin/` is the only password login. `USERNAME_FIELD = phone`.
9. **Vite only for `pulse` and `gohar`.** Other themes are plain CSS/JS. Built assets go to `static/themes/{name}/`.
10. **Keep diffs scoped.** Match existing patterns. Do not add README/docs unless asked.

## How to answer questions

- Prefer these context files, then real source if the repo is available.
- Cite real paths (`carts/services/cart.py`, `themes/pulse/cart.html`).
- If unsure whether something is implemented vs stubbed: booking / appointment / rental / POD store types are **stubs**. Zarinpal is implemented; other gateways are enum’d.
- Current local sample store: slug `shop1`, domains `localhost` / `127.0.0.1` / `shop1.local`, admin phone `09120000000`, OTP `12345`.

## File index in this folder

| File | Use when |
|------|----------|
| `01-overview.md` | What the product is, stack, apps |
| `02-architecture.md` | Settings, URLs, middleware, tenancy, plugins |
| `03-domain-models.md` | Models, enums, relationships |
| `04-api.md` | Every Ninja router/endpoint + payloads |
| `05-storefront-themes.md` | Theme engine, pages, HTML/JS contracts, themes list |
| `06-commerce-flows.md` | Cart, checkout, shipping, tax, payment, orders |
| `07-auth.md` | OTP, JWT, roles, /manage/, 2FA |
| `08-conventions.md` | Coding rules, template tags, gotchas |
| `09-dev-ops.md` | Local run, seeds, Docker, tests, Celery |
| `10-file-map.md` | “Read this file first” map |
| `11-current-work.md` | Uncommitted / recent storefront cart-checkout work (Aug 2026) |
