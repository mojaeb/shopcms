# 04 — API (django-ninja)

Base: **`/api/v1/`**  
Swagger: **`/api/v1/docs`**  
Title: “ShopCMS API” v0.1.0  
Registration: `core/api/__init__.py`

Auth: JWT `Authorization: Bearer <access>` and/or Django session (same-origin cookies). JS always sends CSRF + Bearer when present.

Throttle (base): anon 120/min, auth 60/min, otp_send 5/min, refresh 30/min. Development is looser. 429 body is Persian.

Ninja `HttpError` detail is typically a Persian string in `{"detail": "..."}`.

---

## Public / customer

### Health — `/api/v1/health` (no tenant required)

| Method | Path |
|--------|------|
| GET | `/` `/live` `/ready` `/metrics` |

### Store — `/api/v1/store`

| Method | Path |
|--------|------|
| GET | `/current` |
| GET | `/theme/info` |
| GET | `/theme/templates` |

### Auth — `/api/v1/auth`

| Method | Path | Notes |
|--------|------|--------|
| POST | `/phone/lookup` | |
| POST | `/otp/send` | purpose: `login` \| `register` |
| POST | `/otp/verify/login` | 200 tokens or **202** 2FA challenge |
| POST | `/otp/verify/register` | needs store context |
| POST | `/2fa/verify` | after 202 |
| POST | `/token/refresh` | |
| POST | `/logout` | refresh blacklist |
| GET/PATCH | `/me` | JWT |
| POST | `/2fa/setup` `/2fa/enable` `/2fa/disable` | |
| GET | `/devices` | |
| DELETE | `/devices/{device_id}` | |

### Products — `/api/v1/products`

| Method | Path |
|--------|------|
| GET | `/filters` `/categories/list` `/brands/list` |
| GET | `/` (list + query filters) |
| GET | `/{slug}` |

### Cart — `/api/v1/cart`  **add requires login (401)**

| Method | Path | Body |
|--------|------|------|
| GET | `/` | serialized cart |
| GET | `/count` | `{item_count, total}` |
| POST | `/add` | `{product_slug, variant_id?, quantity=1}` |
| POST | `/update` | `{item_id, quantity}` |
| POST | `/remove` | `{item_id}` |
| POST | `/coupon/apply` `/coupon/remove` | `{code}` / none |
| POST | `/gift-card/apply` `/gift-card/remove` | `{code}` / none |

Serialized cart (important keys): `id`, `items[]`, `coupon`, `gift_card`, totals as **strings**, `item_count`, `tax`, `tax_enabled`.

Item: `id`, `product_id`, `product_slug`, `product_name`, `variant_id`, `variant_label`, `quantity`, `unit_price`, `line_total`, `image`, `in_stock`, `max_available`.

### Addresses — `/api/v1/addresses`

| Method | Path |
|--------|------|
| GET | `/` |
| GET | `/checkout-selection` | default or null if 2+ and none default |
| POST | `/` |
| GET/PUT/DELETE | `/{address_id}` |
| POST | `/{address_id}/set-default` |

Fields: full_name, phone, province, city, postal_code, address_line, building_no, unit, label, is_default.

### Shipping — `/api/v1/shipping`

| Method | Path | Body |
|--------|------|------|
| GET | `/methods` | |
| POST | `/calculate` | `{address_id}` → `{quotes: [{method_id, name, price, is_free, estimated_days, …}]}` |

### Taxes — `/api/v1/taxes`

| Method | Path | Body |
|--------|------|------|
| GET | `/settings` | |
| POST | `/preview` | `{shipping_price}` → `{enabled, tax, …}` |

### Payments — `/api/v1/payments`

| Method | Path | Body / notes |
|--------|------|----------------|
| GET | `/gateways` | enabled for this store |
| POST | `/create` | `{gateway, address_id, shipping_method_id, shipping_price}` → includes `payment_url` |
| GET | `/callback/{gateway}/` | Zarinpal query params; **redirects** to `/order/success/` |
| POST | `/webhook/{gateway}/` | |
| GET | `/{tracking_code}` | |
| POST | `/{tracking_code}/verify` | |
| POST | `/{tracking_code}/refund` | store settings auth |

### Orders — `/api/v1/orders` (customer)

| Method | Path |
|--------|------|
| GET | `/` |
| GET | `/{order_id}` |
| GET | `/{order_id}/invoice` |

### Wishlist — `/api/v1/wishlist`

GET `/` `/count` `/check/{product_slug}`  
POST `/add` `/remove` `/toggle`

### Comments — `/api/v1/comments`

GET `/product/{product_slug}` `/mine`  
POST `/` `/like`

### CMS public — `/api/v1/cms`

GET `/menus` `/banners` `/sliders/{slug}` `/pages/{slug}` `/layout`

### Blog public — `/api/v1/blog`

GET `/posts` `/posts/{slug}` `/categories` `/tags` `/posts/{slug}/comments`  
POST `/posts/{slug}/comments`

### Plugins / digital / subscriptions

- GET `/api/v1/plugins/active`
- GET `/api/v1/downloads/` `/{token}`
- GET `/api/v1/subscriptions/` ; POST `/{id}/cancel` `/{id}/renew`

---

## Store admin — `/api/v1/store-admin/*`

Auth: JWT + store permission helpers in `dashboard/authentication_store.py` (`store_admin_auth`, `store_settings_auth`, …). Superuser also allowed.

| Prefix | Resource |
|--------|----------|
| `/store-admin` | dashboard stats, settings (general/tax/payment/shipping/theme/seo), users, team |
| `/store-admin/products` | products, categories, brands, attributes CRUD |
| `/store-admin/orders` | list, status, shipment, meta/statuses |
| `/store-admin/cms` | pages, shortcodes, menus, banners, sliders, layout |
| `/store-admin/discounts` | coupons, gift cards |
| `/store-admin/shipping` | zones, methods, prices, providers |
| `/store-admin/taxes` | settings, rules |
| `/store-admin/comments` | moderate |
| `/store-admin/blog` | posts, categories, tags, comments |
| `/store-admin/files` | upload/list/update/delete, drivers |
| `/store-admin/notifications` | providers, channels, test, logs |
| `/store-admin/plugins` | enable, registry, manifest |
| `/store-admin/digital` | assets, licenses revoke |
| `/store-admin/subscriptions` | plans, list, renew |
| `/store-admin/reports` | summary, sales, customers, products, inventory, payments, shipping |
| `/store-admin/optimization` | cache warm/clear, status |
| `/store-admin/backups` | CRUD + download + restore |
| `/store-admin/audit` | audit logs |

## Super admin — `/api/v1/super-admin/*`

JWT + `is_superuser`. Tenant middleware is **exempt** for this prefix.

| Path | Purpose |
|------|---------|
| GET `/stats` `/themes` `/plugins` `/stores` | lists |
| POST `/stores` | create store |
| GET/PUT/DELETE `/stores/{id}` | |
| domains CRUD under `/stores/{id}/domains` | |
| admins under `/stores/{id}/admins` | |
| plugins under `/stores/{id}/plugins` | |
| tax/payment/shipping settings per store | |
| `/super-admin/backups` | platform backups |

---

## JS fetch convention

Shared storefront JS (`static/js/*.js`):

```
headers: Content-Type application/json, X-CSRFToken from cookie, Authorization Bearer from sessionStorage.access_token
credentials: same-origin
```

On cart add 401 → redirect `/login/?next=…`.
