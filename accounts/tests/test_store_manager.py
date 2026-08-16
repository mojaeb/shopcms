"""Primary store manager assignment and replacement."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from accounts.enums import MembershipStatus, RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.store_manager import StoreManagerService
from tenants.admin import StoreAdmin
from tenants.forms import StoreConfigForm
from tenants.models import Store, Theme


@pytest.fixture
def theme(db):
    return Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)


@pytest.fixture
def store(db, theme):
    return Store.objects.create(
        name="فروشگاه تست",
        slug="manager-shop",
        theme=theme,
        default_theme=theme,
        currency="IRR",
        status="active",
    )


@pytest.fixture
def store_admin_role(db):
    return Role.objects.get_or_create(
        codename="store_admin",
        defaults={"name": "ادمین فروشگاه", "scope": RoleScope.STORE, "is_system": True},
    )[0]


@pytest.mark.django_db
def test_assign_primary_creates_staff_user(store):
    membership = StoreManagerService().assign_primary(
        store,
        phone="09121112233",
        first_name="رضا",
        last_name="مدیری",
    )
    user = membership.user
    assert user.phone == "09121112233"
    assert user.full_name == "رضا مدیری"
    assert user.is_staff is True
    assert membership.is_primary is True
    assert membership.role.codename == "store_admin"
    assert membership.status == MembershipStatus.ACTIVE


@pytest.mark.django_db
def test_assign_primary_replaces_previous_manager(store, store_admin_role):
    service = StoreManagerService()
    first = service.assign_primary(store, phone="09120000001", first_name="اول")
    second = service.assign_primary(store, phone="09120000002", first_name="دوم")

    first.refresh_from_db()
    second.refresh_from_db()
    assert first.is_primary is False
    assert second.is_primary is True
    assert StoreMembership.objects.filter(store=store, is_primary=True).count() == 1
    assert service.get_primary_user(store).phone == "09120000002"


@pytest.mark.django_db
def test_membership_save_keeps_single_primary(store, store_admin_role):
    a = User.objects.create_user(phone="09121110001", is_staff=True)
    b = User.objects.create_user(phone="09121110002", is_staff=True)
    m1 = StoreMembership.objects.create(
        user=a, store=store, role=store_admin_role, is_primary=True, status=MembershipStatus.ACTIVE
    )
    m2 = StoreMembership.objects.create(
        user=b, store=store, role=store_admin_role, is_primary=True, status=MembershipStatus.ACTIVE
    )
    m1.refresh_from_db()
    assert m1.is_primary is False
    assert m2.is_primary is True


@pytest.mark.django_db
def test_normalize_persian_digits_on_assign(store):
    membership = StoreManagerService().assign_primary(store, phone="۰۹۱۲۳۳۳۴۴۴۴")
    assert membership.user.phone == "09123334444"


@pytest.mark.django_db
def test_store_form_assigns_and_replaces_manager(store):
    payload = {
        "name": store.name,
        "slug": store.slug,
        "store_type": store.store_type,
        "status": store.status,
        "theme": store.theme_id,
        "default_theme": store.default_theme_id,
        "currency": "IRR",
        "timezone": "Asia/Tehran",
        "language": "fa",
        "tax_enabled": False,
        "tax_percent": "0",
        "store_manager_phone": "09125556677",
        "store_manager_first_name": "مینا",
        "store_manager_last_name": "کاظمی",
    }
    form = StoreConfigForm(payload, instance=store)
    assert form.is_valid(), form.errors
    form.save()
    form.save_related_config()

    manager = StoreManagerService().get_primary_user(store)
    assert manager is not None
    assert manager.phone == "09125556677"
    assert manager.full_name == "مینا کاظمی"

    payload["store_manager_phone"] = "09125556688"
    payload["store_manager_first_name"] = "نیما"
    payload["store_manager_last_name"] = "رضایی"
    form = StoreConfigForm(payload, instance=store)
    assert form.is_valid(), form.errors
    form.save()
    form.save_related_config()
    assert StoreManagerService().get_primary_user(store).phone == "09125556688"
    assert StoreMembership.objects.filter(store=store, is_primary=True).count() == 1


@pytest.mark.django_db
def test_store_form_without_manager_keys_does_not_clear(store):
    StoreManagerService().assign_primary(store, phone="09127778899", first_name="پایدار")
    payload = {
        "name": store.name,
        "slug": store.slug,
        "store_type": store.store_type,
        "status": store.status,
        "theme": store.theme_id,
        "default_theme": store.default_theme_id,
        "currency": "IRR",
        "timezone": "Asia/Tehran",
        "language": "fa",
        "tax_enabled": False,
        "tax_percent": "0",
    }
    form = StoreConfigForm(payload, instance=store)
    assert form.is_valid(), form.errors
    form.save()
    form.save_related_config()
    assert StoreManagerService().get_primary_user(store).phone == "09127778899"


@pytest.mark.django_db
def test_store_form_empty_phone_clears_primary(store):
    StoreManagerService().assign_primary(store, phone="09126667788")
    payload = {
        "name": store.name,
        "slug": store.slug,
        "store_type": store.store_type,
        "status": store.status,
        "theme": store.theme_id,
        "default_theme": store.default_theme_id,
        "currency": "IRR",
        "timezone": "Asia/Tehran",
        "language": "fa",
        "tax_enabled": False,
        "tax_percent": "0",
        "store_manager_phone": "",
        "store_manager_first_name": "",
        "store_manager_last_name": "",
    }
    form = StoreConfigForm(payload, instance=store)
    assert form.is_valid(), form.errors
    form.save()
    form.save_related_config()
    assert StoreManagerService().get_primary_user(store) is None


@pytest.mark.django_db
def test_store_admin_lists_manager_and_hides_tab_for_staff(store):
    StoreManagerService().assign_primary(
        store, phone="09124445566", first_name="سارا", last_name="احمدی"
    )
    site = AdminSite()
    model_admin = StoreAdmin(Store, site)
    factory = RequestFactory()

    superuser = User.objects.create_superuser(phone="09120001111", password="x")
    request = factory.get("/")
    request.user = superuser
    qs = model_admin.get_queryset(request)
    row = qs.get(pk=store.pk)
    assert model_admin.store_manager_display(row) == "سارا احمدی (09124445566)"

    titles = [fs[0] for fs in model_admin.get_fieldsets(request, store)]
    assert "مدیر فروشگاه" in titles

    staff = User.objects.create_user(phone="09120002222", is_staff=True)
    staff_request = factory.get("/")
    staff_request.user = staff
    staff_titles = [fs[0] for fs in model_admin.get_fieldsets(staff_request, store)]
    assert "مدیر فروشگاه" not in staff_titles
