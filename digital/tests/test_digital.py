"""Digital download tests."""

from datetime import timedelta
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from accounts.enums import RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from digital.enums import LicenseStatus
from digital.models import DownloadLicense, ProductDigitalAsset
from digital.services.digital import DigitalError, DigitalService
from files.services.file import FileService
from orders.models import Order, OrderItem
from orders.services.order import OrderService
from plugins.services.plugin import PluginService
from products.enums import ProductStatus, ProductType
from products.models import Product
from tenants.enums import StoreType
from tenants.models import Domain, Plugin, Store, StorePlugin, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(
        name="Digital Shop",
        slug="digital-shop",
        default_theme=theme,
        status="active",
        store_type=StoreType.DIGITAL_DOWNLOAD,
    )
    Domain.objects.create(store=s, domain="digital.local")
    PluginService().sync_registry_to_db()
    PluginService().install_defaults(s)
    return s


@pytest.fixture
def user(db, store):
    role = Role.objects.create(codename="customer", name="Customer", scope=RoleScope.STORE)
    u = User.objects.create_user(phone="09128887766", phone_verified=True)
    StoreMembership.objects.create(user=u, store=store, role=role)
    return u


@pytest.fixture
def product(store):
    return Product.objects.create(
        store=store,
        name="Ebook",
        slug="ebook",
        product_type=ProductType.DIGITAL,
        status=ProductStatus.ACTIVE,
        base_price=10000,
    )


@pytest.fixture
def media_file(store):
    buffer = BytesIO()
    Image.new("RGB", (100, 100), color=(10, 10, 10)).save(buffer, format="JPEG")
    buffer.seek(0)
    uploaded = SimpleUploadedFile("file.jpg", buffer.read(), content_type="image/jpeg")
    return FileService().upload(store, uploaded, folder="digital")


@pytest.fixture
def asset(store, product, media_file):
    return DigitalService().attach_asset(store, product.id, media_file.id, max_downloads=2, expire_hours=24)


@pytest.fixture
def order_with_item(store, user, product):
    order = Order.objects.create(
        store=store,
        user=user,
        order_number="ORD-TEST01",
        status="paid",
        subtotal=10000,
        total=10000,
    )
    OrderItem.objects.create(
        order=order,
        product_id=product.id,
        product_name=product.name,
        product_slug=product.slug,
        quantity=1,
        unit_price=10000,
        line_total=10000,
    )
    return order


@pytest.fixture
def auth_headers(user, store):
    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "digital.local"}


@pytest.mark.django_db
def test_attach_asset(store, product, media_file):
    asset = DigitalService().attach_asset(store, product.id, media_file.id)
    assert ProductDigitalAsset.objects.filter(product=product).count() == 1
    product.refresh_from_db()
    assert product.product_type == ProductType.DIGITAL


@pytest.mark.django_db
def test_issue_licenses_for_order(store, user, asset, order_with_item):
    licenses = DigitalService().issue_licenses_for_order(order_with_item)
    assert len(licenses) == 1
    lic = licenses[0]
    assert lic.max_downloads == 2
    assert lic.expires_at is not None


@pytest.mark.django_db
def test_download_limit_exhausted(store, user, asset, order_with_item):
    service = DigitalService()
    lic = service.issue_licenses_for_order(order_with_item)[0]
    service.record_download(lic)
    service.record_download(lic)
    lic.refresh_from_db()
    assert lic.status == LicenseStatus.EXHAUSTED
    with pytest.raises(DigitalError):
        service.validate_download(lic.token)


@pytest.mark.django_db
def test_license_expires(store, user, asset, order_with_item):
    service = DigitalService()
    lic = service.issue_licenses_for_order(order_with_item)[0]
    lic.expires_at = timezone.now() - timedelta(hours=1)
    lic.save(update_fields=["expires_at"])
    with pytest.raises(DigitalError):
        service.validate_download(lic.token)


@pytest.mark.django_db
def test_list_downloads_api(client, auth_headers, asset, order_with_item):
    DigitalService().issue_licenses_for_order(order_with_item)
    response = client.get("/api/v1/downloads/", **auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_download_file_view(client, asset, order_with_item):
    lic = DigitalService().issue_licenses_for_order(order_with_item)[0]
    response = client.get(f"/download/{lic.token}/", HTTP_HOST="digital.local")
    assert response.status_code == 200
    lic.refresh_from_db()
    assert lic.download_count == 1
