# 07 — Auth & roles

Full narrative also lives in `docs/AUTH.md`.

## Methods

| Method | Who | Where | Mechanism |
|--------|-----|-------|-----------|
| OTP phone | customer, store staff, superuser | `/login/`, `/register/` | 5-digit OTP + JWT + Django session |
| Django Admin | staff/superuser | `/admin/` | phone + **password** |
| TOTP 2FA | users with 2FA on | after OTP verify | HTTP 202 + `/api/v1/auth/2fa/verify` |

**Does not exist:** email/password storefront login, username login, social OAuth.

`User.USERNAME_FIELD = "phone"`.

## OTP flow

1. `POST /api/v1/auth/otp/send` `{phone, purpose: login|register}`
2. `POST /api/v1/auth/otp/verify/login` or `/otp/verify/register`
3. Tokens stored in **`sessionStorage`**: `access_token`, `refresh_token` (see `static/js/auth.js`)
4. Django session also established for HTML
5. Redirect: staff → often `/manage/`; customer → `/dashboard/` or `?next=`

OTP: 5 digits, ~2 minutes, max 5 verify attempts. Rate limited.

### Development

```
OTP_USE_FIXED_CODE=True
OTP_FIXED_CODE=12345
```

Any phone logs in with `12345`. No real SMS.

Seed store admin:

| Field | Value |
|-------|--------|
| Phone | `09120000000` |
| OTP | `12345` |
| Role | `store_admin` on `shop1` |

```
http://localhost:8000/login/?next=/manage/
```

## JWT vs session

- HTML `/manage/` and storefront account pages: **Django session**
- JS calling `/api/v1/*`: **Bearer** from sessionStorage + cookies (CSRF, session)
- Store-admin APIs: Bearer + permission auth in `dashboard/authentication_store.py`
- Super-admin APIs: Bearer + `is_superuser`
- `/api/v1/super-admin/` is tenant-middleware **exempt**

## Roles

**Platform:** `is_superuser` / `is_staff` on User.

**Store membership roles (typical):** `store_admin`, `manager`, `content`, `products`, `orders`, `reports`, `support`, `customer`.

`PermissionService().is_store_staff(user, store)` drives `is_store_staff` in templates.

Superuser can use store-admin APIs even without membership.

## 2FA

If enabled: `otp/verify/login` returns **202** + `challenge_token`. Then `POST /api/v1/auth/2fa/verify`. Setup/enable/disable under `/api/v1/auth/2fa/*`.

## Register

Register OTP requires **store context** (tenant host). Creates customer membership on current store.

## Security extras

- Refresh logout blacklists token
- UserDevice list/revoke
- AuditLog for admin actions
- APIRateLimitMiddleware + Ninja throttles
