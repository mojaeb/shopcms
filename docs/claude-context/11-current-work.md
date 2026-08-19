# 11 — Current work snapshot (16 Aug 2026)

This is a **point-in-time** note of uncommitted / in-progress storefront work when this pack was generated. It will go stale; prefer `git status` / `git diff` in the real repo.

## Dirty / untracked (from git status at generation)

**Modified**
- `static/js/cart.js`
- `themes/nextshop/partials/theme.css.html`

**Untracked / new (typical of a cart+checkout pass across themes)**
- `static/js/checkout.js` (also listed as untracked duplicate path on Windows)
- Theme `cart.html` / `checkout.html` for: `default`, `gohar`, `minimal`, `modern`, `nextshop`, `pulse`
- `themes/pulse/product.html`, `themes/pulse/src/main.js`, `themes/pulse/src/modules/gallery.js`, `themes/pulse/src/styles/main.css`
- Built pulse assets: `static/themes/pulse/css/theme.css`, `js/theme.js`, `.vite/manifest.json`
- `logs/shopcms.log` — **do not treat as source of truth; do not commit secrets**

## What this likely means

A cross-theme **cart and checkout polish** is in flight:

- Shared behavior still lives in `static/js/cart.js` and `static/js/checkout.js`.
- Each theme got its own `cart.html` / `checkout.html` so layout/CSS can differ while **keeping the DOM IDs** (`#cart-page`, `#checkout-page`, `#cart-container`, `#checkout-submit`, …).
- Pulse also has PDP/gallery source changes + a Vite rebuild.
- Nextshop theme CSS partial was edited (cart/checkout visual tokens).

`cart.js` treats **pulse** and **nextshop** as “polished” themes (richer item markup + Lucide refresh).

If Claude is asked to “finish cart/checkout”:
1. Diff `static/js/cart.js` and `checkout.js` against HEAD.
2. Diff each theme’s `cart.html`/`checkout.html` vs `themes/default`.
3. Do not drop required IDs.
4. Rebuild pulse (`themes/pulse` → `npm run build`) if `src/` changed.
5. Same for gohar if its Vite src changed.

## Local runtime at generation

A `py .\manage.py runserver` was active in the user’s Windows environment. Default storefront: `http://localhost:8000/` (shop1).

## Known product gaps (not bugs)

- Gateways other than Zarinpal: enum only
- Booking / appointment / rental / POD: stubs
- No storefront email/password or OAuth
- CORS/SPA frontend is future (`CORS_ALLOWED_ORIGINS` placeholder)
