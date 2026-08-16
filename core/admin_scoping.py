"""Django admin queryset scoping by store staff membership.

Store managers with ``is_staff`` must only see/mutate objects for stores they
are assigned to. Superusers remain unrestricted.
"""

from __future__ import annotations

from django.db.models import ForeignKey, Q, QuerySet

from accounts.services.permissions import PermissionService
from tenants.models import Store

# Models without a direct ``store`` FK → lookup path to the related store.
RELATED_STORE_LOOKUPS: dict[str, str] = {
    "products.Inventory": "product__store",
    "orders.Shipment": "order__store",
    "orders.Invoice": "order__store",
    "orders.OrderItem": "order__store",
    "orders.OrderHistory": "order__store",
    "files.FileThumbnail": "media_file__store",
    "comments.CommentLike": "comment__store",
    "carts.CouponUsage": "coupon__store",
    "carts.GiftCardUsage": "gift_card__store",
    "subscriptions.SubscriptionRenewal": "subscription__store",
    "shipping.ShippingPrice": "method__store",
    "shipping.ShippingRule": "method__store",
}

# Platform-wide models: non-superuser store staff must not manage these.
PLATFORM_ONLY_LABELS: frozenset[str] = frozenset(
    {
        "tenants.Theme",
        "tenants.Plugin",
        "accounts.Role",
        "accounts.Permission",
        "accounts.OTPCode",
    }
)

STORE_MODEL_LABEL = "tenants.Store"
USER_MODEL_LABEL = "accounts.User"


def resolve_store_lookup(model) -> str | None:
    """Return ORM lookup to filter by store, ``\"pk\"`` for Store, or None."""
    label = model._meta.label
    if label == STORE_MODEL_LABEL:
        return "pk"
    if label in RELATED_STORE_LOOKUPS:
        return RELATED_STORE_LOOKUPS[label]
    for field in model._meta.fields:
        if field.name == "store" and isinstance(field, ForeignKey):
            remote = getattr(field.remote_field, "model", None)
            if remote is Store or (
                getattr(remote, "_meta", None) and remote._meta.label == STORE_MODEL_LABEL
            ):
                return "store"
    return None


def scope_queryset_for_user(qs: QuerySet, user, store_lookup: str | None) -> QuerySet:
    """Filter a queryset to the user's staff stores (or none)."""
    if not user or not getattr(user, "is_authenticated", False):
        return qs.none()
    if user.is_superuser:
        return qs
    if store_lookup is None:
        return qs

    store_ids = PermissionService().get_staff_store_ids(user)
    if not store_ids:
        return qs.none()

    if store_lookup == "pk":
        return qs.filter(pk__in=store_ids)

    # Inventory may attach via product or variant→product.
    if qs.model._meta.label == "products.Inventory":
        return qs.filter(
            Q(product__store_id__in=store_ids) | Q(variant__product__store_id__in=store_ids)
        ).distinct()

    return qs.filter(**{f"{store_lookup}_id__in": store_ids})


def object_belongs_to_user_stores(obj, user, store_lookup: str | None) -> bool:
    if user.is_superuser:
        return True
    if store_lookup is None or obj is None:
        return False
    store_ids = PermissionService().get_staff_store_ids(user)
    if not store_ids:
        return False
    if store_lookup == "pk":
        return obj.pk in store_ids

    if obj._meta.label == "products.Inventory":
        product = getattr(obj, "product", None)
        if product is not None and product.store_id in store_ids:
            return True
        variant = getattr(obj, "variant", None)
        if variant is not None and getattr(variant, "product", None) is not None:
            return variant.product.store_id in store_ids
        return False

    current = obj
    for part in store_lookup.split("__"):
        current = getattr(current, part, None)
        if current is None:
            return False
    store_id = current.pk if hasattr(current, "pk") else current
    return store_id in store_ids


def _bound_original(model_admin, name: str):
    """Return the unbound original method from the class MRO (pre-patch)."""
    for cls in type(model_admin).mro():
        if name in cls.__dict__ and not getattr(cls.__dict__[name], "_shopcms_scoped", False):
            return cls.__dict__[name]
    return getattr(type(model_admin), name)


def patch_model_admin(model_admin, store_lookup: str | None) -> None:
    if getattr(model_admin, "_shopcms_store_scoped", False):
        return
    model_admin._shopcms_store_scoped = True
    model_admin._shopcms_store_lookup = store_lookup

    original_get_queryset = _bound_original(model_admin, "get_queryset")

    def get_queryset(self, request):
        qs = original_get_queryset(self, request)
        return scope_queryset_for_user(qs, request.user, store_lookup)

    get_queryset._shopcms_scoped = True  # type: ignore[attr-defined]
    model_admin.get_queryset = get_queryset.__get__(model_admin, type(model_admin))

    for perm_name in ("has_view_permission", "has_change_permission", "has_delete_permission"):
        original_perm = _bound_original(model_admin, perm_name)

        def make_perm(orig):
            def has_perm(self, request, obj=None):
                if not orig(self, request, obj):
                    return False
                if obj is None or request.user.is_superuser:
                    return True
                return object_belongs_to_user_stores(obj, request.user, store_lookup)

            has_perm._shopcms_scoped = True  # type: ignore[attr-defined]
            return has_perm

        patched = make_perm(original_perm)
        setattr(model_admin, perm_name, patched.__get__(model_admin, type(model_admin)))

    original_formfield = _bound_original(model_admin, "formfield_for_foreignkey")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "store" and not request.user.is_superuser:
            store_ids = PermissionService().get_staff_store_ids(request.user)
            kwargs["queryset"] = Store.objects.filter(pk__in=store_ids)
        return original_formfield(self, db_field, request, **kwargs)

    formfield_for_foreignkey._shopcms_scoped = True  # type: ignore[attr-defined]
    model_admin.formfield_for_foreignkey = formfield_for_foreignkey.__get__(
        model_admin, type(model_admin)
    )


def patch_platform_only_admin(model_admin) -> None:
    """Restrict platform models to superusers when the user is store staff."""
    if getattr(model_admin, "_shopcms_platform_restricted", False):
        return
    model_admin._shopcms_platform_restricted = True

    for perm_name in (
        "has_module_permission",
        "has_view_permission",
        "has_add_permission",
        "has_change_permission",
        "has_delete_permission",
    ):
        original_perm = _bound_original(model_admin, perm_name)

        def make_perm(orig):
            def has_perm(self, request, *args, **kwargs):
                user = request.user
                if user.is_superuser:
                    return orig(self, request, *args, **kwargs)
                if PermissionService().get_staff_store_ids(user):
                    return False
                return orig(self, request, *args, **kwargs)

            has_perm._shopcms_scoped = True  # type: ignore[attr-defined]
            return has_perm

        patched = make_perm(original_perm)
        setattr(model_admin, perm_name, patched.__get__(model_admin, type(model_admin)))


def patch_user_admin(model_admin) -> None:
    """Limit User changelist to users who belong to the manager's stores."""
    if getattr(model_admin, "_shopcms_store_scoped", False):
        return
    model_admin._shopcms_store_scoped = True

    original_get_queryset = _bound_original(model_admin, "get_queryset")

    def get_queryset(self, request):
        qs = original_get_queryset(self, request)
        if request.user.is_superuser:
            return qs
        store_ids = PermissionService().get_staff_store_ids(request.user)
        if not store_ids:
            return qs.none()
        return qs.filter(memberships__store_id__in=store_ids).distinct()

    get_queryset._shopcms_scoped = True  # type: ignore[attr-defined]
    model_admin.get_queryset = get_queryset.__get__(model_admin, type(model_admin))


def apply_store_admin_scoping() -> None:
    """Patch all registered ModelAdmins for store membership scoping."""
    from django.contrib import admin

    for model, model_admin in list(admin.site._registry.items()):
        label = model._meta.label
        if label in PLATFORM_ONLY_LABELS:
            patch_platform_only_admin(model_admin)
            continue
        if label == USER_MODEL_LABEL:
            patch_user_admin(model_admin)
            continue
        lookup = resolve_store_lookup(model)
        if lookup is None:
            continue
        patch_model_admin(model_admin, lookup)
