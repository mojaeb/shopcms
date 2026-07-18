"""Django Ninja API configuration."""

from ninja import NinjaAPI
from ninja.errors import Throttled

from core.api.health import router as health_router
from core.api.optimization import router as optimization_router
from core.api.backup import router as backup_router
from core.api.backup_platform import router as backup_platform_router
from core.api.audit import router as audit_router
from tenants.api.store import router as store_router
from accounts.api.auth import router as auth_router
from dashboard.api.super_admin import router as super_admin_router
from dashboard.api.store_admin import router as store_admin_router
from cms.api.public import router as cms_public_router
from cms.api.admin import router as cms_admin_router
from products.api.public import router as products_public_router
from products.api.admin import router as products_admin_router
from carts.api.cart import router as cart_router
from carts.api.admin import router as discounts_admin_router
from addresses.api.addresses import router as addresses_router
from shipping.api.public import router as shipping_public_router
from shipping.api.admin import router as shipping_admin_router
from payments.api.payments import router as payments_router
from orders.api.public import router as orders_public_router
from orders.api.admin import router as orders_admin_router
from taxes.api.public import router as taxes_public_router
from taxes.api.admin import router as taxes_admin_router
from wishlists.api.wishlist import router as wishlist_router
from comments.api.public import router as comments_public_router
from comments.api.admin import router as comments_admin_router
from blog.api.public import router as blog_public_router
from blog.api.admin import router as blog_admin_router
from files.api.admin import router as files_admin_router
from notifications.api.admin import router as notifications_admin_router
from plugins.api.admin import router as plugins_admin_router
from plugins.api.public import router as plugins_public_router
from digital.api.public import router as digital_public_router
from digital.api.admin import router as digital_admin_router
from subscriptions.api.public import router as subscriptions_public_router
from subscriptions.api.admin import router as subscriptions_admin_router
from reports.api.admin import router as reports_admin_router

api = NinjaAPI(
    title="ShopCMS API",
    version="0.1.0",
    description="Multi-tenant Commerce Platform API",
    docs_url="/docs",
)


@api.exception_handler(Throttled)
def throttle_exceeded(request, exc: Throttled):
    wait = int(exc.wait) if exc.wait is not None else 60
    return api.create_response(
        request,
        {"detail": f"تعداد درخواست بیش از حد مجاز است. حدود {wait} ثانیه دیگر دوباره تلاش کنید."},
        status=429,
    )


api.add_router("/health", health_router, tags=["Health"])
api.add_router("/store-admin/optimization", optimization_router, tags=["Store Admin Optimization"])
api.add_router("/store-admin/backups", backup_router, tags=["Store Admin Backups"])
api.add_router("/store-admin/audit", audit_router, tags=["Store Admin Security"])
api.add_router("/store", store_router, tags=["Store"])
api.add_router("/auth", auth_router, tags=["Auth"])
api.add_router("/super-admin", super_admin_router, tags=["Super Admin"])
api.add_router("/super-admin/backups", backup_platform_router, tags=["Super Admin Backups"])
api.add_router("/store-admin", store_admin_router, tags=["Store Admin"])
api.add_router("/cms", cms_public_router, tags=["CMS"])
api.add_router("/store-admin/cms", cms_admin_router, tags=["Store Admin CMS"])
api.add_router("/products", products_public_router, tags=["Products"])
api.add_router("/store-admin/products", products_admin_router, tags=["Store Admin Products"])
api.add_router("/cart", cart_router, tags=["Cart"])
api.add_router("/store-admin/discounts", discounts_admin_router, tags=["Store Admin Discounts"])
api.add_router("/addresses", addresses_router, tags=["Addresses"])
api.add_router("/shipping", shipping_public_router, tags=["Shipping"])
api.add_router("/store-admin/shipping", shipping_admin_router, tags=["Store Admin Shipping"])
api.add_router("/payments", payments_router, tags=["Payments"])
api.add_router("/orders", orders_public_router, tags=["Orders"])
api.add_router("/store-admin/orders", orders_admin_router, tags=["Store Admin Orders"])
api.add_router("/taxes", taxes_public_router, tags=["Taxes"])
api.add_router("/store-admin/taxes", taxes_admin_router, tags=["Store Admin Taxes"])
api.add_router("/wishlist", wishlist_router, tags=["Wishlist"])
api.add_router("/comments", comments_public_router, tags=["Comments"])
api.add_router("/store-admin/comments", comments_admin_router, tags=["Store Admin Comments"])
api.add_router("/blog", blog_public_router, tags=["Blog"])
api.add_router("/store-admin/blog", blog_admin_router, tags=["Store Admin Blog"])
api.add_router("/store-admin/files", files_admin_router, tags=["Store Admin Files"])
api.add_router("/store-admin/notifications", notifications_admin_router, tags=["Store Admin Notifications"])
api.add_router("/store-admin/plugins", plugins_admin_router, tags=["Store Admin Plugins"])
api.add_router("/plugins", plugins_public_router, tags=["Plugins"])
api.add_router("/downloads", digital_public_router, tags=["Downloads"])
api.add_router("/store-admin/digital", digital_admin_router, tags=["Store Admin Digital"])
api.add_router("/subscriptions", subscriptions_public_router, tags=["Subscriptions"])
api.add_router("/store-admin/subscriptions", subscriptions_admin_router, tags=["Store Admin Subscriptions"])
api.add_router("/store-admin/reports", reports_admin_router, tags=["Store Admin Reports"])
