"""Tests for store-scoped access (admin + API + permissions)."""

import pytest
from django.contrib import admin
from django.contrib.auth.models import Permission as DjangoPermission
from django.test import RequestFactory

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.jwt import JWTService
from accounts.services.permissions import PermissionService
from core.admin_scoping import (
    apply_store_admin_scoping,
    object_belongs_to_user_stores,
    scope_queryset_for_user,
)
from products.models import Product
from tenants.models import Domain, Store, Theme


@pytest.fixture
def theme(db):
    return Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)


@pytest.fixture
def store1(db, theme):
    store = Store.objects.create(name="Shop One", slug="shop1", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="shop1.test", is_primary=True)
    return store


@pytest.fixture
def store2(db, theme):
    store = Store.objects.create(name="Shop Two", slug="shop2", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="shop2.test", is_primary=True)
    return store


@pytest.fixture
def store_admin_role(db):
    return Role.objects.create(
        name="Store Admin",
        codename="store_admin",
        scope=RoleScope.STORE,
        is_system=True,
    )


@pytest.fixture
def manager_role(db):
    return Role.objects.create(
        name="Manager",
        codename="manager",
        scope=RoleScope.STORE,
        is_system=True,
    )


@pytest.fixture
def manager_of_store1(db, store1, store_admin_role):
    user = User.objects.create_user(
        phone="09121110001",
        first_name="Manager",
        is_staff=True,
    )
    # Grant Django model perms so /admin/ changelist is reachable.
    for codename in ("view_product", "change_product", "view_store", "change_store"):
        perm = DjangoPermission.objects.filter(codename=codename).first()
        if perm:
            user.user_permissions.add(perm)
    StoreMembership.objects.create(
        user=user,
        store=store1,
        role=store_admin_role,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
    )
    return user


@pytest.fixture
def products(db, store1, store2):
    p1 = Product.objects.create(
        store=store1,
        name="P1",
        slug="p1",
        base_price=1000,
        status="active",
    )
    p2 = Product.objects.create(
        store=store2,
        name="P2",
        slug="p2",
        base_price=2000,
        status="active",
    )
    return p1, p2


@pytest.mark.django_db
def test_get_staff_store_ids_single_and_multi(manager_of_store1, store1, store2, manager_role):
    svc = PermissionService()
    assert svc.get_staff_store_ids(manager_of_store1) == {store1.id}

    StoreMembership.objects.create(
        user=manager_of_store1,
        store=store2,
        role=manager_role,
        status=MembershipStatus.ACTIVE,
    )
    assert svc.get_staff_store_ids(manager_of_store1) == {store1.id, store2.id}


@pytest.mark.django_db
def test_can_manage_store_denies_other_store(manager_of_store1, store1, store2):
    svc = PermissionService()
    assert svc.can_manage_store(manager_of_store1, store1) is True
    assert svc.can_manage_store(manager_of_store1, store2) is False
    assert svc.is_store_staff(manager_of_store1, store2) is False


@pytest.mark.django_db
def test_admin_queryset_scopes_products(manager_of_store1, products, store1, store2):
    apply_store_admin_scoping()
    p1, p2 = products
    model_admin = admin.site._registry[Product]
    rf = RequestFactory()
    request = rf.get("/admin/products/product/")
    request.user = manager_of_store1

    qs = model_admin.get_queryset(request)
    ids = set(qs.values_list("id", flat=True))
    assert p1.id in ids
    assert p2.id not in ids

    assert object_belongs_to_user_stores(p1, manager_of_store1, "store") is True
    assert object_belongs_to_user_stores(p2, manager_of_store1, "store") is False
    assert model_admin.has_change_permission(request, p2) is False
    assert model_admin.has_change_permission(request, p1) is True


@pytest.mark.django_db
def test_admin_store_list_scoped(manager_of_store1, store1, store2):
    apply_store_admin_scoping()
    model_admin = admin.site._registry[Store]
    rf = RequestFactory()
    request = rf.get("/admin/tenants/store/")
    request.user = manager_of_store1

    qs = model_admin.get_queryset(request)
    ids = set(qs.values_list("id", flat=True))
    assert ids == {store1.id}


@pytest.mark.django_db
def test_store_staff_cannot_open_django_admin(client, store1, store_admin_role):
    user = User.objects.create_user(phone="09121117777", is_staff=True, password="x")
    StoreMembership.objects.create(
        user=user,
        store=store1,
        role=store_admin_role,
        status=MembershipStatus.ACTIVE,
        is_primary=True,
    )
    apply_store_admin_scoping()
    client.force_login(user)

    store_resp = client.get("/admin/tenants/store/")
    assert store_resp.status_code == 302
    assert "/admin/login/" in store_resp.headers.get("Location", "")

    index_resp = client.get("/admin/")
    assert index_resp.status_code == 302
    assert "/admin/login/" in index_resp.headers.get("Location", "")


@pytest.mark.django_db
def test_admin_multi_store_assignment(manager_of_store1, store1, store2, manager_role, products):
    apply_store_admin_scoping()
    StoreMembership.objects.create(
        user=manager_of_store1,
        store=store2,
        role=manager_role,
        status=MembershipStatus.ACTIVE,
    )
    p1, p2 = products
    model_admin = admin.site._registry[Product]
    rf = RequestFactory()
    request = rf.get("/admin/products/product/")
    request.user = manager_of_store1

    qs = model_admin.get_queryset(request)
    ids = set(qs.values_list("id", flat=True))
    assert ids == {p1.id, p2.id}


@pytest.mark.django_db
def test_superuser_sees_all_stores(store1, store2, products):
    apply_store_admin_scoping()
    superuser = User.objects.create_superuser(phone="09120009999", password="x")
    p1, p2 = products
    model_admin = admin.site._registry[Product]
    rf = RequestFactory()
    request = rf.get("/admin/products/product/")
    request.user = superuser

    qs = model_admin.get_queryset(request)
    ids = set(qs.values_list("id", flat=True))
    assert p1.id in ids and p2.id in ids


@pytest.mark.django_db
def test_scope_queryset_helper(manager_of_store1, products):
    p1, p2 = products
    qs = scope_queryset_for_user(Product.objects.all(), manager_of_store1, "store")
    assert set(qs.values_list("id", flat=True)) == {p1.id}


@pytest.mark.django_db
def test_store_admin_api_rejects_other_store_host(client, manager_of_store1, store1, store2):
    membership = StoreMembership.objects.get(user=manager_of_store1, store=store1)
    token = JWTService().create_tokens(
        manager_of_store1.id, store1.id, "store_admin", membership.id
    ).access_token

    # Token for store1 must not work on store2 host.
    response = client.get(
        "/api/v1/store-admin/dashboard",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_HOST="shop2.test",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_store_admin_api_allows_assigned_store(client, manager_of_store1, store1):
    membership = StoreMembership.objects.get(user=manager_of_store1, store=store1)
    token = JWTService().create_tokens(
        manager_of_store1.id, store1.id, "store_admin", membership.id
    ).access_token

    response = client.get(
        "/api/v1/store-admin/dashboard",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_HOST="shop1.test",
    )
    assert response.status_code == 200
    assert response.json()["store_slug"] == "shop1"


@pytest.mark.django_db
def test_store_admin_api_multi_store_tokens(client, manager_of_store1, store1, store2, manager_role):
    membership2 = StoreMembership.objects.create(
        user=manager_of_store1,
        store=store2,
        role=manager_role,
        status=MembershipStatus.ACTIVE,
    )
    token2 = JWTService().create_tokens(
        manager_of_store1.id, store2.id, "manager", membership2.id
    ).access_token

    response = client.get(
        "/api/v1/store-admin/dashboard",
        HTTP_AUTHORIZATION=f"Bearer {token2}",
        HTTP_HOST="shop2.test",
    )
    assert response.status_code == 200
    assert response.json()["store_slug"] == "shop2"


@pytest.mark.django_db
def test_jwt_without_store_id_rejected(client, manager_of_store1, store1):
    token = JWTService().create_tokens(manager_of_store1.id).access_token
    response = client.get(
        "/api/v1/store-admin/dashboard",
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_HOST="shop1.test",
    )
    assert response.status_code == 401
