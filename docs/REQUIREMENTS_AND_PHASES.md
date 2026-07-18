# پلتفرم چند فروشگاهی Django

**User:** Anonymous  
**Created:** 7/9/2026 22:04:31  
**Updated:** 7/9/2026 23:12:09  
**Exported:** 7/9/2026 23:50:03  
**Link:** [https://chatgpt.com/c/6a4fe7fd-d4dc-83eb-b62e-d0a041c7ea04](https://chatgpt.com/c/6a4fe7fd-d4dc-83eb-b62e-d0a041c7ea04)  

## Prompt:
7/9/2026, 10:04:30 PM

من کارم برنامه نویسیه و پروژه های سایت های فروشگاهی هم دارم مشکلی که دارم اینه که هر بار باید معماری و برنامه نویسی کنم که زمان بره میخوام با استفاده از django و cursor یک برنامه multi tenant درست کنم که فقط دیزاین صفحات رو تغییر بدم.
یک پنل سوپر ادمین باشد که در ان فروشگاه را تعریف کنم نوع ان را تعریف کنم و کاربر ادمین ان فروشگاه را تعریف کنم مدیریت دامنه ها و غیره
سپس فولدری که در ان تم وجود دارد را در یک پوشه خاص بذارم در صورتی که مثلا صفحه single product نداشت از صفحه پیشفرض بگیرد

انواع فروشگاه میتواند:
فروشگاه کالای فیزیکی + پست
فروشگاه کالای دیجیتال + دانلود
فروشگاه کالای دیجیتال + خرید اشتراک
فروشگاه رزرو + خرید خدمت (نسخه بعد)
فروشگاه رزرو + نوبت (نسخه بعد)
فروشگاه اجاره (نسخه بعد)
فروشگاه کالا سفارشی مثل چاپ لباس (نسخه بعد)

در فروشگاه کالا فیزیکی ارسال با پست میخواهم به این صورت باشد: 
صفحات:
- خانه
- فیلتر
- کالا
- وبلاگ ها
- وبلاگ
- سبد خرید
- تسویه
- داشبورد کاربر
- پروفایل و ویرایش پروفایل
- لیست علاقه مندی ها
- سفارشات
- رسید ها و فاکتور ها
- کامنت ها
- آدرس ها

سیستم کارکرد به این صورت است که کالا ها به صورت ajax به سبد اضافه میشوند و به همان صورت از سبد کم یا اضافه میشوند. در صفحه تسویه کاربر میتواند آدرس خود را اضافه کند و اگر قبلا اضافه کرده بود به صورت پیشفرض ادرس قبلی انتخاب شده قرار میگیرد اگر دو تا آدرس یا بیشتر بود هیچکدام را انتخاب نکند تا کاربر انتخاب کند مدل ارسال هم باید انتخاب شود مثلا تیپاکس و پست در تنظیمات فروشگاه میتوان انتخاب کرد که که چه نوع ارسالی میخواهد مثلا ارسال میتواند پست باشد اما متغیر نباشد و ثابت باشد اما ارسال میتواند پست باشد فقط مبلغ را بر اسال مسافت محاسبه کند که از یک json یا دیتابیس میگیرد که از چه شهری تا چه شهری چقدر میشود و میتواند پست باشد که هم مسافت بگیرد و هم وزن بگیرد همینطور برای تیپاکس همینطور و بقیه مدل های پست همچنین میتواند نوع درگاه خود را انتخاب کند و پرداخت کند، نوع درگاه در تنظیمات فروشگاه توسط سوپر ادمین ویرایش میشود و فروشگاه میتواند چند درگاه داشته باشد 
همینطور سوپر ادمین میتواند انتخاب کند که فروش محصولات در اخر مالیات هم اضافه کند یا نه

## Response:
7/9/2026, 10:04:32 PM

ایده‌ای که داری از نظر معماری، اگر درست طراحی شود، می‌تواند تبدیل به یک هسته (Core) شود که تمام فروشگاه‌های آینده‌ات را فقط با تغییر Theme و چند تنظیمات اجرا کنی. اگر قرار است این پروژه را با **Django + Cursor** بسازی، پیشنهاد می‌کنم اصلاً به آن به چشم "فروشگاه" نگاه نکنی؛ بلکه آن را به عنوان یک **Commerce Platform** طراحی کنی.

---

# معماری کلی

```
platform/
│
├── core/                # هسته سیستم
├── accounts/            # کاربران
├── tenants/             # فروشگاه ها
├── products/
├── orders/
├── carts/
├── shipping/
├── payments/
├── taxes/
├── discounts/
├── inventory/
├── comments/
├── wishlist/
├── blogs/
├── cms/
├── notifications/
├── files/
├── themes/
├── plugins/
└── dashboard/
```

---

# Multi Tenant

هر فروشگاه:

```
Store
--------
id
name
slug
store_type
theme
currency
timezone
language
status
tax_enabled
tax_percent
default_theme
created_at
```

هر درخواست:

```
shop1.com
↓

Domain

↓

Store

↓

Theme

↓

Settings

↓

Response
```

---

# دامنه

```
Domain

id
store
domain
is_primary
ssl
redirect
active
```

مثلاً

```
apple.com

shop.apple.com

apple.ir
```

همه به یک Store اشاره می‌کنند.

---

# Super Admin

فقط سوپرادمین می‌تواند:

- ساخت فروشگاه
- حذف فروشگاه
- انتخاب نوع فروشگاه
- انتخاب Theme
- اتصال دامنه
- تعریف ادمین فروشگاه
- فعال کردن پلاگین‌ها
- انتخاب درگاه‌ها
- انتخاب سیستم ارسال
- انتخاب مالیات
- انتخاب ارز
- فعال/غیرفعال کردن امکانات

---

# Store Admin

ادمین فروشگاه فقط موارد خودش را می‌بیند.

مثلاً:

```
Products

Orders

Customers

Discounts

Settings

Blog

Comments

Reports
```

---

# Store Types

```
Physical Goods

Digital Download

Subscription

Booking

Appointment

Rental

Print On Demand
```

هر کدام یک Plugin است.

---

# Theme System

این قسمت مهم‌ترین بخش پروژه است.

```
themes/

default/

home.html

product.html

cart.html

checkout.html

blog.html

...

modern/

home.html

product.html

checkout.html

minimal/

home.html
```

لودر صفحه:

```
اول:

themes/current/product.html

اگر نبود:

themes/default/product.html
```

مثل Laravel View Finder.

---

# صفحات

```
Home

Category

Product

Search

Cart

Checkout

Order Success

Dashboard

Wishlist

Addresses

Invoices

Orders

Comments

Profile

Blog List

Blog Single

404

500
```

---

# CMS

برای هر صفحه:

```
SEO

Meta

Scripts

Header

Footer

Menus

Banners
```

---

# Product

```
Product

Category

Brand

Variant

Attribute

Attribute Value

Image

Video

SEO
```

---

# Variant

```
Tshirt

Color

Red

Blue

Green

Size

L

XL
```

---

# Inventory

```
Warehouse

Inventory

Stock History

Reservation
```

---

# Cart

Ajax کامل.

```
POST

/cart/add

/cart/update

/cart/remove
```

تمام عملیات بدون Refresh.

---

# Checkout

مراحل:

```
سبد

↓

آدرس

↓

روش ارسال

↓

درگاه

↓

پرداخت
```

---

# Address

```
نام

موبایل

استان

شهر

کدپستی

آدرس

پلاک

واحد
```

اگر:

```
یک آدرس
```

همان انتخاب شود.

اگر:

```
دو آدرس
```

هیچکدام انتخاب نشود.

---

# Shipping Engine

این قسمت را Plugin محور بساز.

```
Shipping Provider
```

مثلاً:

```
Post

Tipax

Peyk

Personal Delivery

Free Shipping
```

هر Provider یک کلاس دارد.

```
calculate()

↓

price
```

---

## مدل محاسبه

```
Fixed

Distance

Weight

Distance + Weight

API
```

---

مثلاً

```
مشهد

↓

تهران

↓

۱۸۰ هزار
```

از JSON یا Database.

---

یا

```
۳ کیلو

↓

تهران

↓

۲۲۰ هزار
```

---

یا

```
Distance

+

Weight
```

---

# Payment

Plugin محور.

```
Zarinpal

IDPay

NextPay

Mellat

Pasargad
```

هر کدام:

```
Create Payment

Verify

Refund
```

---

فروشگاه می‌تواند چند درگاه داشته باشد.

```
زرین پال

ملت

آیدی پی
```

کاربر انتخاب کند.

---

# Tax

```
Enabled

Disabled
```

اگر فعال بود:

```
Subtotal

+

Tax

=

Total
```

---

# Discount

```
Coupon

Gift

Percentage

Fixed

First Purchase

Category

Product

User
```

---

# Orders

```
Pending

Waiting Payment

Paid

Preparing

Sent

Delivered

Canceled

Refunded
```

---

# Invoice

```
PDF

Print

Download
```

---

# Notifications

```
SMS

Email

Push

Telegram
```

---

# Permission

RBAC

```
Manager

Content

Products

Orders

Reports

Support
```

---

# Plugin System

```
plugins/

physical/

digital/

subscription/

booking/

shipping/

payments/
```

هر Plugin فقط قابلیت خودش را اضافه کند.

---

# پیشنهاد ساختار دیتابیس

### Core

```
Store
Domain
Theme
Setting
Plugin
```

### Users

```
User
Role
Permission
Address
```

### Product

```
Category
Product
Variant
Brand
Attribute
Gallery
Inventory
```

### Order

```
Cart
CartItem

Order

OrderItem

Shipment

Payment

Invoice
```

### CMS

```
Page

Blog

Comment

Menu

Banner
```

### Marketing

```
Coupon

Discount

GiftCard
```

### Shipping

```
ShippingMethod

ShippingRule

ShippingZone

ShippingPrice
```

### Payment

```
Gateway

Transaction
```

## چند پیشنهاد برای آینده

برای اینکه این پروژه در بلندمدت مقیاس‌پذیر بماند، چند ویژگی را از ابتدا در معماری در نظر بگیر:

- **Hook و Event System** (مثل `order.created`، `payment.success`، `product.updated`) تا افزونه‌ها بدون تغییر هسته بتوانند به رویدادها واکنش نشان دهند.
- **Feature Flags** برای فعال یا غیرفعال کردن قابلیت‌ها در هر فروشگاه (مثلاً وبلاگ، علاقه‌مندی، مالیات، چندانباره، کیف پول).
- **Settings Schema** به‌جای ذخیره تنظیمات پراکنده، تا هر Plugin تنظیمات خودش را داشته باشد.
- **REST API و GraphQL** از ابتدا روی هسته، تا بعداً اپ موبایل یا پنل‌های دیگر بدون تغییر منطق کسب‌وکار اضافه شوند.
- **Background Jobs** با Celery و Redis برای ارسال پیامک، ایمیل، ساخت فاکتور PDF و همگام‌سازی سفارش‌ها.
- **Cache** برای صفحات عمومی، تنظیمات فروشگاه و لیست محصولات.

با این معماری، در آینده برای ساخت یک فروشگاه جدید فقط کافی است:
1. فروشگاه را در پنل سوپرادمین ایجاد کنی.
2. نوع فروشگاه (Physical، Digital، Subscription و...) را انتخاب کنی.
3. تم را داخل پوشه `themes/` قرار دهی.
4. دامنه را متصل کنی.
5. درگاه و روش‌های ارسال را فعال کنی.

در بیشتر موارد، دیگر نیازی به نوشتن کد جدید برای هر پروژه نخواهی داشت و تنها با طراحی قالب و پیکربندی، فروشگاه جدید آماده خواهد شد.

## Prompt:
7/9/2026, 11:09:03 PM

فاز بندی کن تا به cursor بدم

## Response:
7/9/2026, 11:09:05 PM

اگر هدفت این است که **Cursor بتواند مرحله به مرحله پروژه را بسازد**، بهترین روش این است که پروژه را به فازهای کوچک و مستقل تقسیم کنی. هر فاز باید قابل اجرا و تست باشد و تا پایان هر فاز پروژه Run شود.

---

# فاز ۰ - زیرساخت پروژه

### هدف
ساخت اسکلت پروژه

### تسک‌ها

- ایجاد پروژه Django
- تنظیمات Production و Development
- PostgreSQL
- Redis
- Celery
- Django Ninja API
- WhiteNoise
- محیط Docker
- تنظیمات ENV
- Logging
- Health Check
- Static
- Media
- ساخت Base App

---

# فاز ۱ - هسته Multi Tenant

### هدف

پشتیبانی از چند فروشگاه

### تسک‌ها

- Store Model
- Domain Model
- Theme Model
- Store Settings
- Store Type
- Middleware تشخیص دامنه
- Current Store Context
- Store Cache
- Store Activation
- Theme Resolver

در پایان:

```
shop1.com

↓

Store

↓

Theme
```

باید کار کند.

---

# فاز ۲ - سیستم کاربران

### تسک‌ها

- User
- Login OTP
- Register OTP
- Session
- JWT
- Roles
- Permissions
- Store Admin
- Customer

---

# فاز ۳ - پنل Super Admin

### امکانات

- ساخت فروشگاه
- حذف فروشگاه
- اتصال دامنه
- انتخاب Theme
- انتخاب Store Type
- ساخت Admin فروشگاه
- فعال کردن Plugin
- تنظیمات مالیات
- تنظیمات پرداخت
- تنظیمات ارسال

---

# فاز ۴ - پنل مدیریت فروشگاه

### امکانات

Dashboard

آمار

تنظیمات

کاربران

محصولات

سفارشات

کامنت

وبلاگ

گزارش

---

# فاز ۵ - Theme Engine

### مهم‌ترین قسمت پروژه

ساخت سیستم قالب

```
themes/

default/

modern/

minimal/
```

اگر فایل وجود داشت

```
themes/current/product.html
```

لود شود.

اگر نبود

```
themes/default/product.html
```

لود شود.

---

# فاز ۶ - CMS

### امکانات

صفحات

منو

بنر

اسلایدر

SEO

Header

Footer

Blocks

Widgets

---

# فاز ۷ - سیستم محصولات

### مدل‌ها

Category

Brand

Product

Variant

Attribute

Gallery

Video

Inventory

Tags

SEO

---

# فاز ۸ - جستجو و فیلتر

### امکانات

فیلتر Ajax

برند

قیمت

ویژگی

مرتب سازی

Pagination

Search

---

# فاز ۹ - سبد خرید

### امکانات

Ajax

افزودن

حذف

کم کردن

زیاد کردن

کوپن

ذخیره Session

ذخیره User

Merge Guest Cart

---

# فاز ۱۰ - آدرس‌ها

### امکانات

CRUD

Default Address

چند آدرس

اعتبارسنجی

---

# فاز ۱۱ - سیستم ارسال

### بسیار مهم

Plugin Based

Provider

```
Post

Tipax

Peyk

Free

API
```

Engine

```
Fixed

Distance

Weight

Distance + Weight

API
```

Rules

Shipping Zone

Shipping Price

Shipping Method

---

# فاز ۱۲ - پرداخت

### Plugin

زرین پال

IDPay

ملت

پاسارگاد

Verify

Refund

Webhook

چند درگاه

---

# فاز ۱۳ - سفارشات

### مدل‌ها

Order

Order Item

Status

Shipment

History

Tracking

Invoice

PDF

---

# فاز ۱۴ - مالیات

### امکانات

فعال

غیرفعال

درصد

Rule

---

# فاز ۱۵ - تخفیف

Coupon

Gift

Percentage

Fixed

Category

Product

User

First Purchase

Expiration

---

# فاز ۱۶ - علاقه‌مندی

Wishlist

Ajax

---

# فاز ۱۷ - کامنت

Review

Rating

Like

Reply

Moderation

---

# فاز ۱۸ - وبلاگ

Category

Blog

Tags

SEO

Comments

---

# فاز ۱۹ - فایل‌ها

Upload

Image

Video

Thumbnail

Storage

---

# فاز ۲۰ - اعلان‌ها

Email

SMS

Push

Webhook

Telegram

---

# فاز ۲۱ - Plugin System

سیستم افزونه

```
plugins/

physical

digital

subscription

booking

appointment

rental

print_on_demand
```

هر Plugin بتواند

Model

Views

API

Admin

Template

Settings

را اضافه کند.

---

# فاز ۲۲ - فروشگاه کالای دیجیتال

دانلود فایل

مجوز دانلود

Expire

Limit

---

# فاز ۲۳ - فروشگاه اشتراک

Subscription

Recurring

Expire

Renew

---

# فاز ۲۴ - گزارش‌ها

فروش

مشتری

محصول

موجودی

پرداخت

ارسال

---

# فاز ۲۵ - بهینه‌سازی

Redis

Cache

Celery

Optimization

Indexes

Query Optimization

---

# فاز ۲۶ - امنیت

Rate Limit

CSRF

XSS

SQL Injection

Audit Log

2FA

Device Login

---

# فاز ۲۷ - تست

Unit Test

API Test

Integration Test

Load Test

---

# فاز ۲۸ - استقرار

Docker

Nginx

Gunicorn

CI/CD

Backup

Monitoring

---

## پیشنهاد مهم برای کار با Cursor

به‌جای اینکه همه این فازها را یکجا به Cursor بدهی، هر فاز را به **تسک‌های کوچک ۳ تا ۸ ساعته** تقسیم کن. برای هر تسک از Cursor بخواه:

- ابتدا معماری و ساختار پوشه‌ها را طراحی کند.
- سپس مدل‌ها (Models) را پیاده‌سازی کند.
- بعد سرویس‌ها (Services) را بنویسد.
- سپس APIها را ایجاد کند.
- بعد تست‌های واحد (Unit Test) را بنویسد.
- در پایان مستندات همان فاز را تکمیل کند.

این روش باعث می‌شود کیفیت خروجی Cursor بسیار بهتر باشد و مدیریت پروژه هم ساده‌تر شود.

## Prompt:
7/9/2026, 11:11:52 PM

Hook و Event System (مثل order.created، payment.success، product.updated) تا افزونه‌ها بدون تغییر هسته بتوانند به رویدادها واکنش نشان دهند.
Feature Flags برای فعال یا غیرفعال کردن قابلیت‌ها در هر فروشگاه (مثلاً وبلاگ، علاقه‌مندی، مالیات، چندانباره، کیف پول).
Settings Schema به‌جای ذخیره تنظیمات پراکنده، تا هر Plugin تنظیمات خودش را داشته باشد.
REST API و GraphQL از ابتدا روی هسته، تا بعداً اپ موبایل یا پنل‌های دیگر بدون تغییر منطق کسب‌وکار اضافه شوند.
Background Jobs با Celery و Redis برای ارسال پیامک، ایمیل، ساخت فاکتور PDF و همگام‌سازی سفارش‌ها.
Cache برای صفحات عمومی، تنظیمات فروشگاه و لیست محصولات.

این موارد هم میخوام داشته باشه

## Response:
7/9/2026, 11:11:53 PM

اتفاقاً اگر از ابتدا این قابلیت‌ها را در Core قرار بدهی، بعدها تقریباً هیچ‌وقت مجبور نمی‌شوی هسته را تغییر بدهی. من معماری را کمی کامل‌تر می‌کنم تا تبدیل به یک **SaaS Commerce Platform** واقعی شود.

# فاز ۰ - Foundation (قبل از هر چیزی)

این فاز باید پایه کل پروژه باشد.

## Architecture

- Clean Architecture
- Service Layer
- Repository Pattern
- Dependency Injection
- Domain Driven Design (تا حد نیاز)
- Event Bus
- Plugin System
- Theme Engine
- Multi Tenant
- Feature Flag
- Settings Engine

---

# فاز ۱ - Core Framework

### Core

- Config Manager
- Settings Manager
- Feature Flags
- Event Dispatcher
- Hook Manager
- Plugin Loader
- Theme Loader
- Cache Manager
- Storage Manager
- Background Task Manager

---

# فاز ۲ - Event & Hook System

هدف این است که هیچ افزونه‌ای Core را تغییر ندهد.

مثلاً:

```
order.created

order.updated

order.paid

order.cancelled

payment.created

payment.success

payment.failed

product.created

product.updated

product.deleted

user.registered

user.login

cart.updated

shipment.created

shipment.delivered

invoice.created
```

هر Plugin بتواند روی این Eventها Listener ثبت کند.

مثلاً:

```
Payment Plugin

↓

payment.success

↓

Create Invoice

↓

Send SMS

↓

Reduce Inventory
```

یا

```
Affiliate Plugin

↓

order.created

↓

Create Commission
```

---

# فاز ۳ - Feature Flag

هر فروشگاه Featureهای خودش را داشته باشد.

مثلاً

```
Blog

Wishlist

Coupon

Wallet

Gift Card

Comments

Tax

Inventory

Subscription

Download

Multi Vendor

POS

API

GraphQL
```

هر فروشگاه فقط قابلیت‌های فعال را ببیند.

---

# فاز ۴ - Settings Engine

به جای صدها جدول تنظیمات

```
Payment Setting

Shipping Setting

Sms Setting

Tax Setting
```

همه از یک Engine استفاده کنند.

مثلاً

```
Plugin

↓

Schema

↓

Validation

↓

Store Values
```

مثلاً

```
shipping.post.price

shipping.tipax.api_key

payment.zarinpal.merchant

payment.idpay.api_key

sms.kavenegar.api

theme.logo

theme.colors

tax.enabled
```

هر Plugin خودش Schema تنظیماتش را معرفی کند.

---

# فاز ۵ - Plugin SDK

هر Plugin بتواند اضافه کند:

- Model
- API
- Event
- Settings
- Admin Menu
- Permissions
- Theme Components
- Celery Tasks
- Signals

---

# فاز ۶ - REST API

از همان ابتدا

```
/api/v1/
```

تمام Business Logic فقط در Service Layer باشد.

API فقط Service را صدا بزند.

بعداً پنل React

یا Flutter

یا موبایل

همان Serviceها را استفاده کنند.

---

# فاز ۷ - GraphQL

از ابتدا GraphQL هم فعال باشد.

مثلاً

```
products

categories

orders

customer

cart
```

بدون نوشتن دوباره Business Logic.

---

# فاز ۸ - Background Jobs

Celery + Redis

Jobها

```
ارسال پیامک

ارسال ایمیل

ساخت PDF

ساخت Thumbnail

پردازش تصویر

Sync Inventory

Webhook

Export Excel

Import Excel

پاکسازی Cache

پردازش سفارش
```

---

# فاز ۹ - Cache Layer

Cache فقط Redis نباشد.

یک Cache Manager داشته باش.

```
Settings Cache

Store Cache

Product Cache

Category Cache

Menu Cache

Theme Cache

Feature Cache
```

Invalidate خودکار هنگام تغییر داده.

---

# فاز ۱۰ - Search Engine

از ابتدا Interface داشته باشد.

فعلاً

```
Postgres
```

بعداً

```
Meilisearch

Elasticsearch

Typesense
```

فقط Driver عوض شود.

---

# فاز ۱۱ - Storage Driver

Interface

```
Local

MinIO

S3

Cloudflare R2
```

---

# فاز ۱۲ - Payment Driver

Interface

```
Zarinpal

IDPay

Mellat

Pasargad

Stripe

Paypal
```

---

# فاز ۱۳ - Shipping Driver

Interface

```
Post

Tipax

Peyk

Snap

Free

Manual
```

---

# فاز ۱۴ - Notification Driver

```
SMS

Email

Telegram

Push

Webhook
```

---

# فاز ۱۵ - Audit Log

ثبت تمام عملیات

```
کاربر

چه کاری

روی چه چیزی

کی

از چه IP

از چه Device
```

---

# فاز ۱۶ - Permission Engine

RBAC

```
Role

Permission

Policy

Scope

Store

Object Permission
```

---

# فاز ۱۷ - Workflow Engine

مثلاً سفارش

```
Pending

↓

Paid

↓

Preparing

↓

Packing

↓

Sent

↓

Delivered
```

هر Plugin بتواند State جدید اضافه کند.

---

# فاز ۱۸ - Scheduler

Cron داخلی

مثلاً

```
Expire Subscription

Send Reminder

Delete Temp Files

Backup

Generate Report
```

---

# فاز ۱۹ - Webhook System

هر فروشگاه بتواند Webhook تعریف کند.

```
order.created

↓

POST

↓

https://example.com/webhook
```

---

# فاز ۲۰ - Marketplace SDK

بعداً بتوانی Marketplace بسازی.

Plugin نصب شود.

Theme نصب شود.

Shipping نصب شود.

Payment نصب شود.

---

## نتیجه نهایی

اگر این فازها را از ابتدا پیاده‌سازی کنی، خروجی فقط یک فروشگاه اینترنتی نخواهد بود؛ بلکه یک **پلتفرم SaaS ماژولار** خواهی داشت که می‌تواند انواع فروشگاه‌های فیزیکی، دیجیتال، اشتراکی، رزرو، اجاره و خدماتی را با هسته‌ای مشترک اجرا کند. برای پروژه‌های جدید معمولاً فقط کافی است یک Theme جدید، چند Plugin و تنظیمات فروشگاه را اضافه کنی، بدون اینکه نیاز به تغییر در Core داشته باشی. این معماری در بلندمدت هزینه نگهداری و توسعه را به شکل چشمگیری کاهش می‌دهد.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)