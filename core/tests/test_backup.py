"""Backup and restore tests."""

import json
import zipfile

import pytest
from django.test import Client

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from core.enums import BackupScope, BackupStatus
from core.models import BackupJob
from core.services.backup import BackupService, RestoreService
from products.enums import ProductStatus
from products.models import Product
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="Backup Shop", slug="backup-shop", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="backup.local")
    return store


@pytest.fixture
def backup_role(db):
    role = Role.objects.create(codename="manager", name="Manager", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="backup.manage", name="Backup", group="settings")
    role.permissions.add(perm)
    return role


@pytest.fixture
def staff_user(db, store, backup_role):
    user = User.objects.create_user(phone="09123330000", phone_verified=True, is_staff=True)
    StoreMembership.objects.create(user=user, store=store, role=backup_role, status=MembershipStatus.ACTIVE)
    return user


@pytest.fixture
def auth_headers(staff_user, store):
    token = JWTService().create_tokens(staff_user.id, store.id, "manager", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "backup.local"}


@pytest.fixture
def sample_product(store):
    return Product.objects.create(
        store=store,
        name="Backup Product",
        slug="backup-product",
        status=ProductStatus.ACTIVE,
        base_price=50000,
    )


@pytest.mark.django_db
def test_create_store_backup(store, sample_product, settings, tmp_path):
    settings.BACKUP_ROOT = tmp_path
    job = BackupService().create_store_backup(store, include_media=False)

    assert job.status == BackupStatus.COMPLETED
    assert job.record_count > 0
    assert job.file_path
    with zipfile.ZipFile(job.file_path, "r") as zf:
        manifest = json.loads(zf.read("manifest.json"))
        data = json.loads(zf.read("data.json"))
    assert manifest["store_slug"] == store.slug
    assert any(item["model"] == "products.product" for item in data)


@pytest.mark.django_db
def test_restore_store_round_trip(store, sample_product, settings, tmp_path):
    settings.BACKUP_ROOT = tmp_path
    backup_service = BackupService()
    restore_service = RestoreService()

    job = backup_service.create_store_backup(store, include_media=False)
    Product.objects.filter(store=store).delete()
    assert Product.objects.filter(store=store).count() == 0

    result = restore_service.restore_store_backup(
        store,
        job.file_path,
        confirm_slug=store.slug,
    )
    assert result["restored_records"] > 0
    assert Product.objects.filter(store=store, slug="backup-product").exists()


@pytest.mark.django_db
def test_restore_dry_run(store, sample_product, settings, tmp_path):
    settings.BACKUP_ROOT = tmp_path
    job = BackupService().create_store_backup(store, include_media=False)
    result = RestoreService().restore_store_backup(store, job.file_path, dry_run=True)
    assert result["dry_run"] is True
    assert result["record_count"] > 0


@pytest.mark.django_db
def test_backup_api(client: Client, auth_headers, store, sample_product, settings, tmp_path):
    settings.BACKUP_ROOT = tmp_path

    create = client.post(
        "/api/v1/store-admin/backups/",
        data=json.dumps({"include_media": False}),
        content_type="application/json",
        **auth_headers,
    )
    assert create.status_code == 200
    job_id = create.json()["id"]

    listing = client.get("/api/v1/store-admin/backups/", **auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = client.get(f"/api/v1/store-admin/backups/{job_id}", **auth_headers)
    assert detail.status_code == 200
    assert detail.json()["status"] == BackupStatus.COMPLETED

    restore = client.post(
        f"/api/v1/store-admin/backups/{job_id}/restore",
        data=json.dumps({"confirm_slug": store.slug, "dry_run": True}),
        content_type="application/json",
        **auth_headers,
    )
    assert restore.status_code == 200
    assert restore.json()["dry_run"] is True


@pytest.mark.django_db
def test_platform_backup(settings, tmp_path):
    settings.BACKUP_ROOT = tmp_path
    job = BackupService().create_platform_backup()
    assert job.scope == BackupScope.PLATFORM
    assert job.status == BackupStatus.COMPLETED
    assert BackupJob.objects.filter(scope=BackupScope.PLATFORM).count() == 1
