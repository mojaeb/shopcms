"""Tenant URL patterns - storefront pages."""

from django.urls import path, re_path

from tenants.views import seo as seo_views
from tenants.views import store_admin_ui as manage
from tenants.views import storefront as views

urlpatterns = [
    path("robots.txt", seo_views.robots_txt, name="storefront_robots"),
    path("sitemap.xml", seo_views.sitemap_xml, name="storefront_sitemap"),
    re_path(
        r"^google(?P<token>[A-Za-z0-9_-]+)\.html$",
        seo_views.google_html_verification,
        name="storefront_google_verification",
    ),
    path("manage/", manage.manage_dashboard, name="store_admin_dashboard"),
    path("manage/products/", manage.manage_products, name="store_admin_products"),
    path("manage/products/new/", manage.manage_product_new, name="store_admin_product_new"),
    path("manage/products/<int:product_id>/edit/", manage.manage_product_edit, name="store_admin_product_edit"),
    path("manage/files/", manage.manage_files, name="store_admin_files"),
    path("manage/orders/", manage.manage_orders, name="store_admin_orders"),
    path("manage/orders/<int:order_id>/", manage.manage_order_detail, name="store_admin_order_detail"),
    path("manage/settings/", manage.manage_settings, name="store_admin_settings"),
    path("manage/pages/", manage.manage_pages, name="store_admin_pages"),
    path("manage/pages/new/", manage.manage_page_new, name="store_admin_page_new"),
    path("manage/pages/<int:page_id>/edit/", manage.manage_page_edit, name="store_admin_page_edit"),
    path("manage/blog/", manage.manage_blog, name="store_admin_blog"),
    path("manage/blog/new/", manage.manage_blog_new, name="store_admin_blog_new"),
    path("manage/blog/<int:post_id>/edit/", manage.manage_blog_edit, name="store_admin_blog_edit"),
    path("manage/comments/", manage.manage_comments, name="store_admin_comments"),
    path("manage/shortcodes/", manage.manage_shortcodes, name="store_admin_shortcodes"),
    path("", views.storefront_home, name="storefront_home"),
    path("products/", views.storefront_category, name="storefront_category"),
    path("products/<slug:slug>/", views.storefront_category, name="storefront_category_slug"),
    # Legacy redirects from /category/
    path("category/", views.storefront_category_redirect),
    path("category/<slug:slug>/", views.storefront_category_redirect),
    path("product/<slug:slug>/", views.storefront_product, name="storefront_product"),
    path("search/", views.storefront_search, name="storefront_search"),
    path("cart/", views.storefront_cart, name="storefront_cart"),
    path("checkout/", views.storefront_checkout, name="storefront_checkout"),
    path("order/success/", views.storefront_order_success, name="storefront_order_success"),
    path("dashboard/", views.storefront_dashboard, name="storefront_dashboard"),
    path("profile/", views.storefront_profile, name="storefront_profile"),
    path("profile/edit/", views.storefront_profile_edit, name="storefront_profile_edit"),
    path("wishlist/", views.storefront_wishlist, name="storefront_wishlist"),
    path("orders/", views.storefront_orders, name="storefront_orders"),
    path("orders/<int:order_id>/", views.storefront_order_detail, name="storefront_order_detail"),
    path("invoices/", views.storefront_invoices, name="storefront_invoices"),
    path("comments/", views.storefront_comments, name="storefront_comments"),
    path("addresses/", views.storefront_addresses, name="storefront_addresses"),
    path("blog/", views.storefront_blog_list, name="storefront_blog_list"),
    path("blog/<slug:slug>/", views.storefront_blog_single, name="storefront_blog_single"),
    path("login/", views.storefront_login, name="storefront_login"),
    path("register/", views.storefront_register, name="storefront_register"),
    path("downloads/", views.storefront_downloads, name="storefront_downloads"),
    path("subscriptions/", views.storefront_subscriptions, name="storefront_subscriptions"),
    path("page/<slug:slug>/", views.storefront_cms_page, name="storefront_cms_page"),
]
