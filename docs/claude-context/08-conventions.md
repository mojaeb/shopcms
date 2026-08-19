# 08 — Conventions & gotchas

## Code style

- Business logic in `services/`; routers/views stay thin.
- Ninja `Schema` DTOs for request bodies.
- Persian `verbose_name` on models; user-facing errors in Persian.
- Keep PRs/diffs scoped. Do not add markdown the user did not ask for (this `docs/claude-context` folder is an exception because it was requested).
- Match existing naming: `CartService`, `PaymentService`, `ThemeEngine`.

## Tenancy

- Always `get_current_store()` or `request.store`.
- Filter querysets by store. Unique constraints are per-store.
- Super-admin and health paths skip tenant resolution — do not assume `request.store` there.

## Money & i18n

- Integer amounts (toman/IRR). Do not use `decimal_places=2` for product prices.
- Display: `{% money amount %}` or `ShopMoney.formatMoney(value, currency)`.
- Persian digits in UI. `ShopMoney.formatAmount` for counts (cart badge).
- RTL: `dir="rtl"` on html. Test mirrored layouts (qty controls, summaries).

## Auth gotchas

- Add-to-cart **requires login**. Product buttons must not assume guests can add.
- `body` needs `data-authenticated="1"` when `user.is_authenticated` or cart.js will redirect to login even if a session cookie exists without JWT (prefer both).
- CSRF required on POST from JS (`X-CSRFToken`).
- `/admin/` password is independent of OTP users (OTP-only users may have unusable password).

## Theme gotchas

- Changing a template in `pulse` does **not** change `nextshop` unless you edit both (or only `default` if they inherit).
- `ThemeLoader` only serves files that **exist**. Fallback is resolver rewriting the path to `themes/default/...`, not Django’s `{% extends %}` magic across themes. `{% extends "base.html" %}` resolves through the same loader (current theme base, else default).
- Store admin templates are under `templates/store_admin/` and **skip** ThemeLoader.
- Pulse/gohar: after CSS/JS source edits run `npm run build`; Django serves `static/themes/...`.
- `cart.js` special-cases `theme-pulse` and `theme-nextshop` for item markup. Other themes get the simpler HTML branch.
- `checkout.js` bails out if `#checkout-page` is missing — a theme that restyles checkout **must keep that id**.

## Cart/checkout gotchas

- `#cart-container` / `#cart-summary` / `#checkout-page` IDs are API-to-DOM contracts.
- Payment create needs `shipping_method_id` from quote (`method_id`) not a random PK guess from HTML value — checkout.js uses `q.method_id`.
- Order is not created until payment verify succeeds.
- Callback is GET redirect (Zarinpal) — not a JSON SPA route.

## Frontend libraries

- Default/minimal/modern/round: mostly CSS + small JS; some Alpine on product pages.
- Pulse/gohar: Vite, Tailwind v4, Lucide, GSAP, Swiper, HTMX on `window.htmx`.
- Nextshop: Lucide; `window.lucide.createIcons()` after innerHTML injects (cart.js calls `refreshIcons()`).
- Do not introduce React/Vue for storefront unless explicitly requested.

## Plugins

- Booking/appointment/rental/POD are **not full products**. Do not implement a whole booking engine unless asked.
- Feature plugins (blog, comments, …) wrap capabilities that already have first-class apps.

## Admin

- Unfold + `core.admin_navigation.get_navigation`.
- Custom CSS: `static/css/admin-yekan.css`, `admin-unfold-rtl.css`.

## Testing

- `pytest` with `config.settings.test`.
- Prefer factory-boy; don’t hit real Zarinpal.
- When changing cart/checkout JS contracts, update themed templates **and** tests/e2e if they assert IDs.

## What not to do

- Don’t add DRF, email/password storefront login, or LTR-only CSS.
- Don’t hardcode a theme path in Python views — use `ThemeEngine.render_page`.
- Don’t compute payable totals only in JS; server recomputes on `payments/create`.
- Don’t commit `.env`, secrets, `logs/`, or huge media dumps.
- Don’t use `git commit` unless the user asks.
