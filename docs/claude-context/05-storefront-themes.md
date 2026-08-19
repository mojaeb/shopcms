# 05 — Storefront & themes

## How rendering works

1. Store `effective_theme.directory` → folder under `themes/`
2. `ThemeLoader` + `ThemeResolver`: `themes/{current}/page.html` → fallback `themes/default/page.html`
3. Views call `ThemeEngine.render_page(page_key)` using map in `tenants/theme/pages.py`
4. Skip theme loader for prefixes: `admin/`, `django/`, `registration/`, `debug_toolbar/`, `store_admin/`

### Registered page keys (`STOREFRONT_PAGES`)

home, category, product, search, cart, checkout, order_success, dashboard, profile, profile_edit, wishlist, orders, order_detail, invoices, comments, addresses, blog_list, blog_single, auth, downloads, subscriptions, 404, 500.

CMS pages use `cms_page.html` (not in that dict).

### Template tags (builtins — no `{% load %}` needed)

```
{% theme_template "product.html" %}
{% theme_include "header" %}          → partials/header.html via theme resolve
{{ theme_slug|theme_asset:"css/theme.css" }}  → /static/themes/{slug}/css/theme.css
{% money amount %}                    → Persian digits + toman SVG for IRR
{{ value|money_format }}  {{ value|persian_digits }}
```

Toman SVG sprite: `partials/currency_sprite.html` (`#toman`). JS: `static/js/money.js` → `window.ShopMoney.formatMoney / formatAmount`.

### Context always available

`store`, `theme_slug`, `theme_engine`, `theme_settings`, `is_store_staff`, CMS menus/banners/layout, `user`, `seo` when set.

`body` class: `theme-{{ theme_slug }}`.  
If logged in: `data-authenticated="1"` on `<body>` (required by cart.js).

## Theme directories on disk

| Dir | Notes |
|-----|--------|
| `default` | Fallback for every missing template. Must stay complete. |
| `modern` | |
| `minimal` | Fashion/decor RTL reference (`PRODUCT.md` / `DESIGN.md`). IRANYekan, hairline borders, sale red `#db1215` |
| `round` | Default **assigned** to seed store `shop1`. Sellzy-like rounded UI |
| `nextshop` | Teal-trust retail (`design-system/nextshop/`). Lucide. Polished cart/checkout |
| `pulse` | **Vite + Tailwind v4** + Lucide + GSAP + Swiper + HTMX. Polished cart/checkout |
| `gohar` | **Vite + Tailwind v4**. Luxury dark jewelry. Seed: `seed_gohar`. Host `gohar.local` |

Static counterparts: `static/themes/{name}/`.

### Vite themes (pulse, gohar)

```
cd themes/pulse   # or themes/gohar
npm install
npm run dev | npm run build
```

Output: `static/themes/{name}/js/theme.js` + `css/theme.css` + `.vite/manifest.json`.  
**Commit built assets** so Django runtime does not need Node.

## Shared storefront JS (`static/js/`)

Loaded from theme `base.html` (default loads money, toast, cart, wishlist, auth-header).

| File | Role |
|------|------|
| `cart.js` | Add/update/remove, coupon/gift, cart page render, badge `[data-cart-count]` |
| `checkout.js` | Checkout page only if `#checkout-page` exists |
| `auth.js` / `auth-header.js` | OTP login/register, header account state |
| `wishlist.js` | `[data-wishlist-count]` |
| `money.js` | `window.ShopMoney` |
| `toast.js` | `window.ShopToast` |
| `addresses.js`, `orders.js`, `comments.js`, `blog.js`, `profile.js`, `product-filters.js`, `downloads.js`, `subscriptions.js` | page modules |

`cart.js` exposes `window.ShopCart = { addToCart, loadCart, updateCartBadge }`.

Polished cart item HTML is used when `body` has `theme-pulse` or `theme-nextshop`.

## HTML / data contracts (do not break)

### Add to cart

```html
<button data-add-to-cart data-product="{{ product.slug }}" data-variant="" data-quantity="1">
```

- `data-product` = **slug** (not id)
- Optional Alpine `x-data` host: reads `selectedVariant.id` and `qty`
- Optional `data-quantity` (Pulse qty/variants modules)
- Button may contain `<span>` whose text flips to «اضافه شد»
- Requires login (`body[data-authenticated=1]` or `sessionStorage.access_token`)

### Cart page

Must have:

```html
<div id="cart-page" data-currency="{{ store.currency }}">
  <div id="cart-container"></div>
  <div id="cart-summary"></div>
</div>
```

Optional polish: `.ps-cart-layout`, `[data-ps-cart-tools]`.

Cart.js also wires coupon/gift IDs if present: `#coupon-code`, `#apply-coupon`, `#remove-coupon`, `#gift-code`, `#apply-gift`, `#remove-gift`.

### Checkout page

Must have `#checkout-page` with `data-currency`. `checkout.js` **returns immediately** if missing.

Required IDs:

| ID | Role |
|----|------|
| `checkout-address` | address list / empty |
| `checkout-items` | line items |
| `shipping-options` | quotes |
| `payment-gateways` | radios |
| `cart-subtotal` `discount-row` `discount-cost` `applied-code-row` `shipping-cost` `tax-row` `tax-cost` `checkout-total` | totals |
| `checkout-submit` | pay |
| `checkout-message` | status |
| `coupon-code` `apply-coupon` `remove-coupon` `gift-code` `apply-gift` `remove-gift` `coupon-message` | discounts |

Address modal (optional): `[data-modal]`, `[data-modal-dismiss]`, form POST to `/api/v1/addresses/`.

Pay payload:

```json
{
  "gateway": "<code>",
  "address_id": 1,
  "shipping_method_id": 1,
  "shipping_price": 0
}
```

Success: redirect to `data.payment_url`.

### Cart badge

`[data-cart-count]` — hidden when 0. Text is Persian digits via ShopMoney.

### Default base.html pattern

```
html lang=fa dir=rtl
include partials/styles.html, theme.css.html, currency_sprite, cms_header, cms_footer
scripts: money.js, toast.js, cart.js, wishlist.js, auth-header.js
block extra_css / extra_js
```

Pulse/gohar `base.html` instead loads Vite-built `theme.css` / `theme.js` plus the same shared JS as needed.

## Theme authoring rules

1. Override only templates you customize; inherit the rest from `default`.
2. Keep `#cart-page` / `#checkout-page` IDs and data attributes.
3. Do not fork cart/checkout **behavior** into theme JS unless necessary; restyle via CSS/markup that `cart.js` already understands.
4. Persian copy, RTL, toman icon — no `$`, no LTR-only layouts.
5. Anti-clichés (product design): purple gradients, Inter-as-display, cream+terracotta clusters, glassmorphism decoration, emoji icons, eyebrow/kicker labels, nested card stacks. Prefer Lucide if icons are needed.
6. `minimal` design tokens: ink `#141414`, sale `#db1215`, container 1320px, sharp corners, ease `cubic-bezier(0.23, 1, 0.32, 1)`.
7. `nextshop` tokens: teal `#0F766E`, canvas `#F8FAFC`, max 1280px, radius 16–20px. See `design-system/nextshop/DESIGN.md`.
8. `gohar`: ink `#0a0a0a`, gold `#c9a24b`, cream `#f4efe6`, Kalameh type.

## Store admin UI is not a theme

`/manage/` uses `templates/store_admin/*.html`. Do not put those under `themes/`.
