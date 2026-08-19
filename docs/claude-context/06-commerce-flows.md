# 06 — Commerce flows (cart → order)

## Cart

Service: `carts/services/cart.py` (`CartService`). API: `carts/api/cart.py`. JS: `static/js/cart.js`.

- Cart is per store. Identified by **user** if authenticated, else **session_key**.
- Guest cart can exist; **add-to-cart API requires a user** (`_require_user` → 401 «ورود الزامی است»).
- On login, guest cart is merged into user cart (service responsibility).
- Stock checked via Inventory (`track_inventory` + `available`). Error: «موجودی کافی نیست».
- Prices snapshotted onto CartItem (`unit_price`, `line_total`).
- Coupons: percentage or fixed; scope all/category/product.
- Gift cards: apply remaining balance.
- Tax computed via `TaxService.calculate_for_cart` and included in serialize (`tax`, `tax_enabled`).

JS add: `POST /api/v1/cart/add` `{product_slug, variant_id, quantity}` with CSRF + Bearer.

Cart page: if `#cart-page` present, `loadCart()` renders items into `#cart-container` and summary into `#cart-summary`. Qty plus/minus and remove call update/remove APIs.

## Checkout

Page: themed `checkout.html`. JS: `static/js/checkout.js` (only runs if `#checkout-page` exists).

Checkout expects the user to already be authenticated (storefront view should gate this).

Flow:

1. `GET /api/v1/cart/` → line items + subtotal + discount + tax flags
2. `GET /api/v1/addresses/` + `/checkout-selection`
   - 0 addresses → prompt to add
   - 1 address or a default → auto-select
   - 2+ without default → user must pick
3. On address select: `POST /api/v1/shipping/calculate` `{address_id}` → quotes; first quote auto-selected
4. `GET /api/v1/payments/gateways`
5. Tax refresh: `POST /api/v1/taxes/preview` `{shipping_price}`
6. Totals = cart subtotal + shipping + tax (discount already in cart)
7. Pay: `POST /api/v1/payments/create` then `window.location = data.payment_url`

Can pay only when address + shipping + gateway are selected.

Address create from modal: `POST /api/v1/addresses/` with form fields including `is_default`.

## Shipping calculator

`shipping` app. Providers: post, tipax, peyk, free, api.  
Modes: fixed, distance, weight, distance_weight, api.

Quotes include `method_id`, `name`, `price`, `is_free`, `estimated_days`.  
Per-store which methods exist is configured in store admin / StoreSetting shipping group + ShippingMethod rows.

Digital/subscription stores may not need physical shipping; still expect checkout JS to handle empty quotes (shows «روش ارسالی یافت نشد»).

## Tax

Store fields `tax_enabled`, `tax_percent` plus optional `TaxRule`s. Sample seed store: 9% enabled. Preview includes shipping_price so tax can apply to shipping if rules say so.

## Payments

Service: `payments/services/payment.py`. Providers under `payments/providers/` — **Zarinpal implemented**.

`create_payment`:

- Validates gateway enabled for store
- Totals from cart + shipping + tax
- Creates `PaymentTransaction` with metadata (cart snapshot, shipping, address)
- Returns serialize including **`payment_url`** for redirect

Callback `GET /api/v1/payments/callback/{gateway}/`:

- Looks up txn by store + gateway + Authority
- `verify_payment`
- If PAID → `OrderService.create_from_payment` (inside payment service) → redirect `/order/success/?tracking=&ref=&order=`
- Else → `/order/success/?status=failed&tracking=`

Missing txn → `/order/success/?status=failed`.

## Orders

Service: `orders/services/order.py`. Created **from payment**, not from cart POST.

On success typically:

- Order + OrderItems (product snapshots)
- Clear/consume cart, coupon usage, gift card balance
- Shipment / invoice as applicable
- Digital licenses / subscriptions if product types require them

Statuses: pending, waiting_payment, paid, preparing, sent, delivered, canceled, refunded.

Customer HTML: `/orders/`, `/orders/<id>/`, `/invoices/`, `/order/success/`.  
Staff: `/manage/orders/` + `/api/v1/store-admin/orders`.

## Digital & subscriptions (side effects of paid order)

- Digital: `ProductDigitalAsset` + `DownloadLicense`; download URL `/download/<token>/`
- Subscriptions: `CustomerSubscription` from `SubscriptionPlan`; Celery expires them daily 02:00 Tehran

## End-to-end sequence

```
Login (OTP) → JWT + session
Add to cart (AJAX, logged in)
/cart/  manage qty / coupon
/checkout/  address → shipping quote → gateway
POST /payments/create → Zarinpal
callback verify → Order.create_from_payment
/order/success/
```

## Tests related to this flow

- App tests under `carts/tests`, `orders/tests`, `payments/tests`, `shipping/tests`
- Integration: `tests/integration/` (checkout flow)
- E2E smoke: `tests/e2e/`
