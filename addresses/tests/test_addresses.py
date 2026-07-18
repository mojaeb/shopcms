"""Address tests."""

import json

import pytest

from accounts.models import User
from accounts.services.jwt import JWTService
from addresses.models import CustomerAddress
from addresses.services.address import AddressError, AddressService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Address Shop", slug="address-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="addr.local")
    return s


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="09125556677", first_name="Ali", last_name="Test")


@pytest.fixture
def auth_headers(user, store):
    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "addr.local"}


@pytest.fixture
def sample_address(store, user):
    return CustomerAddress.objects.create(
        store=store,
        user=user,
        full_name="Ali Ahmadi",
        phone="09125556677",
        province="خراسان رضوی",
        city="مشهد",
        postal_code="9187945678",
        address_line="بلوار سجاد",
        building_no="12",
        unit="3",
        is_default=True,
    )


ADDRESS_PAYLOAD = {
    "full_name": "Sara Karimi",
    "phone": "09121112233",
    "province": "تهران",
    "city": "تهران",
    "postal_code": "1234567890",
    "address_line": "خیابان ولیعصر",
    "building_no": "5",
    "unit": "2",
}


@pytest.mark.django_db
def test_create_address_api(client, store, user, auth_headers):
    response = client.post(
        "/api/v1/addresses/",
        data=json.dumps(ADDRESS_PAYLOAD),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Sara Karimi"
    assert data["is_default"] is True


@pytest.mark.django_db
def test_list_addresses_api(client, store, user, sample_address, auth_headers):
    response = client.get("/api/v1/addresses/", **auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_update_address_api(client, store, user, sample_address, auth_headers):
    response = client.put(
        f"/api/v1/addresses/{sample_address.id}",
        data=json.dumps({"city": "نیشابور"}),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["city"] == "نیشابور"


@pytest.mark.django_db
def test_delete_address_api(client, store, user, sample_address, auth_headers):
    response = client.delete(f"/api/v1/addresses/{sample_address.id}", **auth_headers)
    assert response.status_code == 200
    assert CustomerAddress.objects.count() == 0


@pytest.mark.django_db
def test_set_default_address(client, store, user, sample_address, auth_headers):
    second = CustomerAddress.objects.create(
        store=store,
        user=user,
        full_name="Second",
        phone="09120000000",
        province="تهران",
        city="تهران",
        postal_code="1111111111",
        address_line="addr 2",
    )
    response = client.post(f"/api/v1/addresses/{second.id}/set-default", **auth_headers)
    assert response.status_code == 200
    sample_address.refresh_from_db()
    second.refresh_from_db()
    assert second.is_default is True
    assert sample_address.is_default is False


@pytest.mark.django_db
def test_validation_invalid_phone(client, store, user, auth_headers):
    payload = {**ADDRESS_PAYLOAD, "phone": "123"}
    response = client.post(
        "/api/v1/addresses/",
        data=json.dumps(payload),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_validation_invalid_postal_code(client, store, user, auth_headers):
    payload = {**ADDRESS_PAYLOAD, "postal_code": "123"}
    response = client.post(
        "/api/v1/addresses/",
        data=json.dumps(payload),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_checkout_selection_single_address(store, user):
    service = AddressService()
    address = CustomerAddress.objects.create(
        store=store, user=user, full_name="A", phone="09121112233",
        province="تهران", city="تهران", postal_code="1234567890", address_line="x",
    )
    selected = service.get_checkout_selection(user, store)
    assert selected.pk == address.pk


@pytest.mark.django_db
def test_checkout_selection_multiple_without_default(store, user):
    service = AddressService()
    CustomerAddress.objects.create(
        store=store, user=user, full_name="A", phone="09121112233",
        province="تهران", city="تهران", postal_code="1234567890", address_line="x",
    )
    CustomerAddress.objects.create(
        store=store, user=user, full_name="B", phone="09122223344",
        province="تهران", city="تهران", postal_code="1234567891", address_line="y",
        is_default=False,
    )
    assert service.get_checkout_selection(user, store) is None


@pytest.mark.django_db
def test_checkout_selection_api(client, store, user, sample_address, auth_headers):
    response = client.get("/api/v1/addresses/checkout-selection", **auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == sample_address.id


@pytest.mark.django_db
def test_addresses_require_auth(client, store):
    response = client.get("/api/v1/addresses/", HTTP_HOST="addr.local")
    assert response.status_code == 401


@pytest.mark.django_db
def test_storefront_addresses_page(client, store, user):
    client.force_login(user)
    response = client.get("/addresses/", HTTP_HOST="addr.local")
    assert response.status_code == 200
    assert "addresses-page" in response.content.decode()
