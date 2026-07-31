"""Store Admin UI shell views (HTML + JS consuming /api/v1/store-admin/)."""

from functools import wraps
from urllib.parse import quote

from django.shortcuts import redirect, render

from accounts.services.permissions import PermissionService
from tenants.context import get_current_store


def store_staff_required(view_func):
    """Require Django session user to be store staff; else redirect to login."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        store = get_current_store() or getattr(request, "store", None)
        if not PermissionService().is_store_staff(request.user, store):
            next_url = quote(request.get_full_path())
            return redirect(f"/login/?next={next_url}")
        return view_func(request, *args, **kwargs)

    return wrapper


def _ctx(request, **extra):
    store = get_current_store() or getattr(request, "store", None)
    theme_colors = {"primary": "#0f766e", "background": "#f8fafc", "text": "#0f172a"}
    if store:
        from tenants.services.theme_settings import ThemeSettingsService

        cfg = ThemeSettingsService().get_theme_settings(store)
        theme_colors = {
            **theme_colors,
            **((cfg.get("colors") if isinstance(cfg, dict) else None) or {}),
        }
    ctx = {
        "store": store,
        "page_title": extra.pop("page_title", "مدیریت فروشگاه"),
        "active_nav": extra.pop("active_nav", ""),
        "theme_colors": theme_colors,
    }
    ctx.update(extra)
    return ctx


@store_staff_required
def manage_dashboard(request):
    return render(
        request,
        "store_admin/dashboard.html",
        _ctx(request, page_title="داشبورد", active_nav="dashboard"),
    )


@store_staff_required
def manage_products(request):
    return render(
        request,
        "store_admin/products.html",
        _ctx(request, page_title="محصولات", active_nav="products"),
    )


@store_staff_required
def manage_product_new(request):
    return render(
        request,
        "store_admin/product_form.html",
        _ctx(
            request,
            page_title="محصول جدید",
            active_nav="products",
            product_id=None,
            is_edit=False,
        ),
    )


@store_staff_required
def manage_product_edit(request, product_id: int):
    return render(
        request,
        "store_admin/product_form.html",
        _ctx(
            request,
            page_title="ویرایش محصول",
            active_nav="products",
            product_id=product_id,
            is_edit=True,
        ),
    )


@store_staff_required
def manage_orders(request):
    return render(
        request,
        "store_admin/orders.html",
        _ctx(request, page_title="سفارشات", active_nav="orders"),
    )


@store_staff_required
def manage_order_detail(request, order_id: int):
    return render(
        request,
        "store_admin/order_detail.html",
        _ctx(
            request,
            page_title=f"سفارش #{order_id}",
            active_nav="orders",
            order_id=order_id,
        ),
    )


@store_staff_required
def manage_files(request):
    return render(
        request,
        "store_admin/files.html",
        _ctx(request, page_title="کتابخانه رسانه", active_nav="files"),
    )


@store_staff_required
def manage_settings(request):
    return render(
        request,
        "store_admin/settings.html",
        _ctx(request, page_title="تنظیمات", active_nav="settings"),
    )


@store_staff_required
def manage_pages(request):
    return render(
        request,
        "store_admin/pages.html",
        _ctx(request, page_title="صفحات", active_nav="pages"),
    )


@store_staff_required
def manage_page_new(request):
    return render(
        request,
        "store_admin/page_form.html",
        _ctx(
            request,
            page_title="صفحه جدید",
            active_nav="pages",
            page_id=None,
            is_edit=False,
        ),
    )


@store_staff_required
def manage_page_edit(request, page_id: int):
    return render(
        request,
        "store_admin/page_form.html",
        _ctx(
            request,
            page_title="ویرایش صفحه",
            active_nav="pages",
            page_id=page_id,
            is_edit=True,
        ),
    )


@store_staff_required
def manage_blog(request):
    return render(
        request,
        "store_admin/blog.html",
        _ctx(request, page_title="وبلاگ", active_nav="blog"),
    )


@store_staff_required
def manage_comments(request):
    return render(
        request,
        "store_admin/comments.html",
        _ctx(request, page_title="مدیریت نظرات", active_nav="comments"),
    )


@store_staff_required
def manage_blog_new(request):
    return render(
        request,
        "store_admin/blog_form.html",
        _ctx(
            request,
            page_title="مقاله جدید",
            active_nav="blog",
            post_id=None,
            is_edit=False,
        ),
    )


@store_staff_required
def manage_blog_edit(request, post_id: int):
    return render(
        request,
        "store_admin/blog_form.html",
        _ctx(
            request,
            page_title="ویرایش مقاله",
            active_nav="blog",
            post_id=post_id,
            is_edit=True,
        ),
    )


@store_staff_required
def manage_shortcodes(request):
    return render(
        request,
        "store_admin/shortcodes.html",
        _ctx(request, page_title="شورت‌کدها", active_nav="shortcodes"),
    )
