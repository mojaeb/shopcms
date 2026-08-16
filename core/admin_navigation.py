"""Unfold sidebar: daily platform items vs collapsed store/customer catalogs."""

from __future__ import annotations

from django.http import HttpRequest
from django.urls import reverse_lazy


def can_access_admin(request: HttpRequest) -> bool:
    user = getattr(request, "user", None)
    return bool(user and getattr(user, "is_authenticated", False) and user.is_staff)


def can_view_model(app_label: str, model_name: str):
    view_perm = f"{app_label}.view_{model_name}"
    change_perm = f"{app_label}.change_{model_name}"

    def _check(request: HttpRequest) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if user.is_superuser:
            return True
        return user.has_perm(view_perm) or user.has_perm(change_perm)

    return _check


def _item(title: str, icon: str, url_name: str, app: str | None = None, model: str | None = None) -> dict:
    item = {
        "title": title,
        "icon": icon,
        "link": reverse_lazy(url_name),
        "permission": can_view_model(app, model) if app and model else can_access_admin,
    }
    return item


def get_navigation(request: HttpRequest | None = None) -> list[dict]:
    """Primary links stay open; store catalog and customer data stay collapsed."""
    return [
        {
            "title": "پلتفرم",
            "collapsible": False,
            "items": [
                _item("داشبورد", "dashboard", "admin:index"),
                _item("فروشگاه‌ها", "storefront", "admin:tenants_store_changelist", "tenants", "store"),
                _item("کاربران", "group", "admin:accounts_user_changelist", "accounts", "user"),
                _item(
                    "مدیرهای فروشگاه",
                    "badge",
                    "admin:accounts_storemembership_changelist",
                    "accounts",
                    "storemembership",
                ),
                _item("تم‌ها", "palette", "admin:tenants_theme_changelist", "tenants", "theme"),
                _item("افزونه‌ها", "extension", "admin:tenants_plugin_changelist", "tenants", "plugin"),
            ],
        },
        {
            "title": "کاتالوگ فروشگاه",
            "separator": True,
            "collapsible": True,
            "items": [
                _item("محصولات", "inventory_2", "admin:products_product_changelist", "products", "product"),
                _item("دسته‌بندی‌ها", "category", "admin:products_category_changelist", "products", "category"),
                _item("برندها", "sell", "admin:products_brand_changelist", "products", "brand"),
                _item("تگ‌ها", "label", "admin:products_tag_changelist", "products", "tag"),
                _item("ویژگی‌ها", "tune", "admin:products_productattribute_changelist", "products", "productattribute"),
                _item("موجودی", "warehouse", "admin:products_inventory_changelist", "products", "inventory"),
                _item(
                    "فایل دیجیتال",
                    "download",
                    "admin:digital_productdigitalasset_changelist",
                    "digital",
                    "productdigitalasset",
                ),
                _item(
                    "طرح اشتراک",
                    "card_membership",
                    "admin:subscriptions_subscriptionplan_changelist",
                    "subscriptions",
                    "subscriptionplan",
                ),
            ],
        },
        {
            "title": "داده‌های مشتری",
            "separator": True,
            "collapsible": True,
            "items": [
                _item("سبدهای خرید", "shopping_cart", "admin:carts_cart_changelist", "carts", "cart"),
                _item("علاقه‌مندی", "favorite", "admin:wishlists_wishlistitem_changelist", "wishlists", "wishlistitem"),
                _item("آدرس‌ها", "location_on", "admin:addresses_customeraddress_changelist", "addresses", "customeraddress"),
                _item("نظرات", "chat", "admin:comments_comment_changelist", "comments", "comment"),
                _item("کدهای OTP", "pin", "admin:accounts_otpcode_changelist", "accounts", "otpcode"),
            ],
        },
        {
            "title": "فروش و مالی",
            "separator": True,
            "collapsible": True,
            "items": [
                _item("سفارش‌ها", "receipt_long", "admin:orders_order_changelist", "orders", "order"),
                _item("ارسال‌ها", "local_shipping", "admin:orders_shipment_changelist", "orders", "shipment"),
                _item("فاکتورها", "request_quote", "admin:orders_invoice_changelist", "orders", "invoice"),
                _item("پرداخت‌ها", "payments", "admin:payments_paymenttransaction_changelist", "payments", "paymenttransaction"),
                _item("کوپن‌ها", "confirmation_number", "admin:carts_coupon_changelist", "carts", "coupon"),
                _item("کارت هدیه", "card_giftcard", "admin:carts_giftcard_changelist", "carts", "giftcard"),
                _item("مالیات", "percent", "admin:taxes_taxrule_changelist", "taxes", "taxrule"),
                _item("روش‌های ارسال", "package_2", "admin:shipping_shippingmethod_changelist", "shipping", "shippingmethod"),
            ],
        },
        {
            "title": "محتوای فروشگاه",
            "separator": True,
            "collapsible": True,
            "items": [
                _item("صفحات", "article", "admin:cms_page_changelist", "cms", "page"),
                _item("منوها", "menu", "admin:cms_menu_changelist", "cms", "menu"),
                _item("بنرها", "image", "admin:cms_banner_changelist", "cms", "banner"),
                _item("اسلایدرها", "view_carousel", "admin:cms_slider_changelist", "cms", "slider"),
                _item("ویجت‌ها", "widgets", "admin:cms_widget_changelist", "cms", "widget"),
                _item("شورت‌کدها", "code", "admin:cms_shortcode_changelist", "cms", "shortcode"),
                _item("مقالات", "newspaper", "admin:blog_blogpost_changelist", "blog", "blogpost"),
                _item("فایل‌ها", "folder", "admin:files_mediafile_changelist", "files", "mediafile"),
            ],
        },
        {
            "title": "سیستم",
            "separator": True,
            "collapsible": True,
            "items": [
                _item("نقش‌ها", "admin_panel_settings", "admin:accounts_role_changelist", "accounts", "role"),
                _item("دسترسی‌ها", "key", "admin:accounts_permission_changelist", "accounts", "permission"),
                _item("دامنه‌ها", "language", "admin:tenants_domain_changelist", "tenants", "domain"),
                _item("تنظیمات فروشگاه", "settings", "admin:tenants_storesetting_changelist", "tenants", "storesetting"),
                _item("افزونه فروشگاه", "extension", "admin:tenants_storeplugin_changelist", "tenants", "storeplugin"),
                _item("پشتیبان‌گیری", "backup", "admin:core_backupjob_changelist", "core", "backupjob"),
                _item("لاگ ممیزی", "history", "admin:core_auditlog_changelist", "core", "auditlog"),
                _item(
                    "اعلان‌ها",
                    "notifications",
                    "admin:notifications_notificationlog_changelist",
                    "notifications",
                    "notificationlog",
                ),
            ],
        },
    ]
