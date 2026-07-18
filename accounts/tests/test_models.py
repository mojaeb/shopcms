"""Tests for user model and roles."""

import pytest

from accounts.enums import RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.permissions import PermissionService
from tenants.models import Store, Theme


@pytest.fixture
def theme(db):
    return Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)


@pytest.fixture
def store(db, theme):
    return Store.objects.create(name="Shop", slug="shop1", default_theme=theme, status="active")


@pytest.fixture
def customer_role(db):
    return Role.objects.create(name="Customer", codename="customer", scope=RoleScope.STORE, is_system=True)


@pytest.fixture
def admin_role(db):
    perm = Permission.objects.create(codename="products.view", name="View Products", group="products")
    role = Role.objects.create(name="Products", codename="products", scope=RoleScope.STORE, is_system=True)
    role.permissions.add(perm)
    return role


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="09121234567", first_name="Ali", last_name="Test")


@pytest.mark.django_db
def test_user_full_name(user):
    assert user.full_name == "Ali Test"


@pytest.mark.django_db
def test_store_membership(user, store, customer_role):
    membership = StoreMembership.objects.create(user=user, store=store, role=customer_role)
    assert membership.is_active
    assert str(membership) == "09121234567 @ shop1 (customer)"


@pytest.mark.django_db
def test_permission_service(user, store, admin_role):
    perm_service = PermissionService()
    membership = StoreMembership.objects.create(user=user, store=store, role=admin_role)

    assert perm_service.has_permission(user, "products.view", store)
    assert not perm_service.has_permission(user, "products.delete", store)
    assert perm_service.has_role(user, "products", store)


@pytest.mark.django_db
def test_superuser_has_all_permissions(user, store):
    user.is_superuser = True
    user.save()
    perm_service = PermissionService()
    assert perm_service.has_permission(user, "anything.here", store)
