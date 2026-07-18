"""Audit log tests."""

import pytest
from django.test import Client

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from core.enums import AuditAction, AuditOutcome
from core.models import AuditLog
from core.services.audit import AuditService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="Audit Shop", slug="audit-shop", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="audit.local")
    return store


@pytest.fixture
def security_role(db):
    role = Role.objects.create(codename="manager", name="Manager", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="security.view", name="Security", group="security")
    role.permissions.add(perm)
    return role


@pytest.fixture
def staff_user(db, store, security_role):
    user = User.objects.create_user(phone="09124440000", phone_verified=True, is_staff=True)
    StoreMembership.objects.create(user=user, store=store, role=security_role, status=MembershipStatus.ACTIVE)
    return user


@pytest.fixture
def auth_headers(staff_user, store):
    token = JWTService().create_tokens(staff_user.id, store.id, "manager", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "audit.local"}


@pytest.mark.django_db
def test_audit_service_writes_log(store):
    service = AuditService()
    user = User.objects.create_user(phone="09125550000")
    log = service.log(
        AuditAction.LOGIN,
        user=user,
        store=store,
        outcome=AuditOutcome.SUCCESS,
        metadata={"test": True},
    )
    assert log is not None
    assert AuditLog.objects.filter(action=AuditAction.LOGIN).count() == 1


@pytest.mark.django_db
def test_audit_api(client: Client, auth_headers, store):
    AuditLog.objects.create(store=store, action=AuditAction.LOGIN, outcome=AuditOutcome.SUCCESS)
    response = client.get("/api/v1/store-admin/audit/", **auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
