# Gohar (گوهر) Theme

Luxury dark jewelry storefront inspired by `_temp/modern-jewelry-website`.

| | |
|---|---|
| **Slug / directory** | `gohar` |
| **Store slug** | `gohar` |
| **Domains** | `gohar.local`, `gohar.localhost` |
| **Stack** | Vite · Tailwind v4 · GSAP · Lucide · Swiper · HTMX |
| **Aesthetic** | ink `#0a0a0a`, gold `#c9a24b`, cream `#f4efe6`, sharp corners |

## Build assets

```bash
cd themes/gohar
npm install
npm run build
```

Output: `static/themes/gohar/css/theme.css` and `static/themes/gohar/js/theme.js`.

## Seed store + catalog

```bash
d:/DEVLIC/ShopCMS/app/.venv/Scripts/python.exe manage.py seed_store
d:/DEVLIC/ShopCMS/app/.venv/Scripts/python.exe manage.py seed_gohar
```

`seed_gohar` creates/updates the store, copies product images from the reference site into `media/gohar/`, seeds 6 categories + 8 products, about/contact pages, and header/footer menus.

## Open locally

1. Map hosts (if needed): `127.0.0.1 gohar.local`
2. Run the server: `d:/DEVLIC/ShopCMS/app/.venv/Scripts/python.exe manage.py runserver`
3. Visit: **http://gohar.local:8000/**

(`ALLOWED_HOSTS` in development includes `.local`.)

## Reference fidelity

**Faithful:** colors, typography (Kalameh), hero copy, marquee, category mosaic, product names/prices/images, atelier story + counters, header/footer chrome, product filter chips, about/contact narrative.

**Approximated:** cart/wishlist/auth/checkout (ShopCMS flows styled in Gohar skin), contact form (mailto + info cards instead of client-only JS form), product related carousel on PDP.
