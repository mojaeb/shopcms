# 03 — Domain models

Convention: almost all business models are **store-scoped**. Unique slugs are usually `(store, slug)`. Money fields: `DecimalField(max_digits=12, decimal_places=0)`. Base: `core.models.TimeStampedModel` (`created_at`, `updated_at`). Soft-delete mixin exists but is not universal.

## tenants

- **Theme:** name, slug, directory (folder under `themes/`), is_active, is_default (only one default)
- **Store:** see architecture. Types: `physical`, `digital_download`, `subscription`, `booking`, `appointment`, `rental`, `print_on_demand`. Status: `active`, `inactive`, `suspended`
- **Domain:** store FK, unique domain, is_primary, ssl, redirect_to_primary
- **StoreSetting:** store, group, key, value (JSON), value_type
- **Plugin / StorePlugin:** platform plugin catalog + per-store enablement

## accounts

- **User:** `USERNAME_FIELD=phone`; email optional; is_staff / is_superuser; phone_verified
- **Permission / Role:** Role has platform|store scope
- **StoreMembership:** user ↔ store ↔ role; status active/inactive/suspended
- **OTPCode:** purpose login|register
- **UserSecuritySettings:** TOTP 2FA
- **UserDevice**

Store roles commonly seeded: `store_admin`, `manager`, `content`, `products`, `orders`, `reports`, `support`, plus `customer`.

## products

- **Tag, Category** (tree), **Brand** — all store-scoped
- **ProductAttribute / ProductAttributeValue** — display types: list, select, color, button
- **Product:** type simple|variable|digital|subscription; status draft|active|inactive; base_price, compare_price; SEO mixin; unique (store, slug)
- **ProductVariant:** price, compare_price, sku, attributes M2M to values
- **ProductImage / ProductVideo** — `is_primary` on image
- **Inventory:** per product or variant; track_inventory, quantity, reserved → `available`, `is_in_stock`

`Product.primary_image` property: primary image URL or first image or `""`.

## carts

- **Cart:** store + (user XOR session_key); coupon FK; gift_card FK
- **CartItem:** product, optional variant, quantity, unit_price, line_total
- **Coupon:** code, discount_type percentage|fixed, value, scope all|category|product
- **GiftCard:** code, balance
- **CouponUsage / GiftCardUsage**

## addresses

**CustomerAddress:** full_name, phone, province, city, postal_code, address_line, building_no, unit, label, is_default. Iran-shaped.

## shipping

- **ShippingZone**
- **ShippingMethod:** provider post|tipax|peyk|free|api; calculation_mode fixed|distance|weight|distance_weight|api
- **ShippingPrice** — city-to-city / weight tables
- **ShippingRule**

## taxes

**TaxRule** — plus store-level `tax_enabled` / `tax_percent` on Store.

## payments

**PaymentTransaction:** gateway, amount, authority, ref_id, tracking_code, status pending|redirected|paid|failed|refunded|cancelled, metadata JSON.

Gateways: `zarinpal`, `idpay`, `mellat`, `pasargad`.

## orders

- **Order:** order_number `ORD-XXXXXXXX`; status pending → waiting_payment → paid → preparing → sent → delivered (also canceled/refunded); OneToOne payment; address_snapshot JSON; money lines (subtotal, discount, shipping_cost, tax, total); coupon/gift codes; customer_note
- **OrderItem:** denormalized snapshot (product_id/name/slug, variant, sku, qty, unit_price, line_total, image)
- **Shipment:** status pending|preparing|shipped|in_transit|delivered|returned
- **OrderHistory**
- **Invoice**

Orders are created **from a paid payment**, not from a “place order” button. Checkout creates a PaymentTransaction; callback creates the Order.

## wishlists / comments / blog

- **WishlistItem:** user + product (+ store)
- **Comment** on product + **CommentLike**
- **BlogCategory, BlogTag, BlogPost, BlogComment**

## cms

SeoFieldsMixin, LayoutSettings, Page, Menu/MenuItem, Banner, Slider/Slide, Widget, ContentBlock, Shortcode.

## files / digital / subscriptions / notifications / core

- **MediaFile, FileThumbnail**
- **ProductDigitalAsset, DownloadLicense** (token download at `/download/<token>/`)
- **SubscriptionPlan, CustomerSubscription, SubscriptionRenewal**
- **NotificationChannel, NotificationLog**
- **BackupJob, AuditLog**

`dashboard` and `reports` have **no models**.

## Relationship sketch

```
Store ─┬─ Domain[]
       ├─ Theme (theme, default_theme)
       ├─ StoreSetting[]
       ├─ StorePlugin[] → Plugin
       ├─ Product[] ─┬─ Variant[] ─ Inventory
       │             ├─ Image[] / Video[]
       │             └─ Category / Brand / Tag / Attributes
       ├─ Cart[] ─ CartItem[] → Product/Variant
       ├─ CustomerAddress[]
       ├─ ShippingMethod[] / Zone / Price
       ├─ PaymentTransaction[] ─ Order (1:1)
       │                         ├─ OrderItem[]
       │                         ├─ Shipment
       │                         └─ Invoice
       ├─ Page / Menu / Banner / Slider / BlogPost / …
       └─ StoreMembership[] → User + Role
```
