"""Restrict Django / Unfold admin to superusers.

Store managers keep ``is_staff`` for /manage/ and store-admin APIs, but must
not open /admin/.
"""

from __future__ import annotations

from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SuperuserAdminAuthenticationForm(AdminAuthenticationForm):
    error_messages = {
        **AdminAuthenticationForm.error_messages,
        "invalid_login": _(
            "فقط حساب سوپرادمین می‌تواند وارد پنل مدیریت شود."
        ),
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError(
                self.error_messages["invalid_login"],
                code="invalid_login",
                params={"username": self.username_field.verbose_name},
            )


def _has_admin_permission(request) -> bool:
    user = getattr(request, "user", None)
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "is_superuser", False)
    )


def patch_admin_superuser_only() -> None:
    """Gate the default AdminSite: views + login form."""
    if getattr(admin.site, "_shopcms_superuser_only", False):
        return
    admin.site.has_permission = _has_admin_permission  # type: ignore[method-assign]
    admin.site.login_form = SuperuserAdminAuthenticationForm
    admin.site._shopcms_superuser_only = True  # type: ignore[attr-defined]
