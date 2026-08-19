"""Tax tests."""

import json
from decimal import Decimal

import pytest

from accounts.enums import RoleScope
from accounts.models import Role, StoreMembership, User
from accounts.services.jwt import JWTService
from carts.models import Cart, CartItem
from products.enums import ProductStatus, ProductType
from products.models import Category, Inventory, Product
from taxes.models import TaxRule
from taxes.services.tax import TaxService
from tenants.models import Domain, Plugin, Store, StorePlugin, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(
        name="Tax Shop", slug="tax-shop", default_theme=theme, status="active",
        tax_enabled=True, tax_percent=Decimal("9"),
    )
    Domain.objects.create(store=s, domain="tax.local")
    plugin, _ = Plugin.objects.get_or_create(codename="tax", defaults={"name": "Tax", "is_active": True})
    StorePlugin.objects.create(store=s, plugin=plugin, is_enabled=True)
    return s


@pytest.fixture
def admin_role(db):
    return Role.objects.create(codename="store_admin", name="Admin", scope=RoleScope.STORE)


@pytest.fixture
def admin_user(db, store, admin_role):
    u = User.objects.create_user(phone="09123334455", phone_verified=True)
    StoreMembership.objects.create(user=u, store=store, role=admin_role)
    return u


@pytest.fixture
def admin_headers(admin_user, store):
    token = JWTService().create_tokens(admin_user.id, store.id, "store_admin", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "tax.local"}


@pytest.fixture
def cart_with_item(store, user):
    product = Product.objects.create(
        store=store, name="Tax Item", slug="tax-item", status=ProductStatus.ACTIVE,
        base_price=1000000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=product, quantity=5)
    cart = Cart.objects.create(store=store, user=user, session_key="tax-cart")
    CartItem.objects.create(cart=cart, product=product, quantity=1, unit_price=1000000)
    return cart


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="09125556677", phone_verified=True)


@pytest.mark.django_db
def test_tax_follows_store_flag_even_without_plugin(store, cart_with_item):
    StorePlugin.objects.filter(store=store).update(is_enabled=False)
    result = TaxService().calculate_for_cart(store, cart_with_item)
    assert result["enabled"] is True
    assert result["tax"] == "90000"

    store.tax_enabled = False
    store.save(update_fields=["tax_enabled"])
    result = TaxService().calculate_for_cart(store, cart_with_item)
    assert result["enabled"] is False
    assert result["tax"] == "0"


@pytest.mark.django_db
def test_save_admin_tax_enables_plugin(store):
    from tenants.services.store_config import StoreConfigService

    store.tax_enabled = True
    store.tax_percent = Decimal("9")
    store.save(update_fields=["tax_enabled", "tax_percent"])
    StorePlugin.objects.filter(store=store, plugin__codename="tax").update(is_enabled=False)

    StoreConfigService().save_admin_data(store, {**StoreConfigService().get_admin_initial(store)})
    assert StorePlugin.objects.get(store=store, plugin__codename="tax").is_enabled is True


@pytest.mark.django_db
def test_default_tax_calculation(store, cart_with_item):
    result = TaxService().calculate_for_cart(store, cart_with_item)
    assert result["enabled"] is True
    assert result["tax"] == "90000"


@pytest.mark.django_db
def test_category_tax_rule(store, cart_with_item):
    category = Category.objects.create(store=store, name="Electronics", slug="electronics")
    product = cart_with_item.items.first().product
    product.category = category
    product.save()

    TaxRule.objects.create(
        store=store, name="Electronics VAT", rate_percent=Decimal("5"),
        scope="category", category=category, is_active=True, priority=10,
    )

    result = TaxService().calculate_for_cart(store, cart_with_item)
    assert result["tax"] == "50000"


@pytest.mark.django_db
def test_tax_preview_api(client, store, user, cart_with_item):
    client.force_login(user)
    response = client.post(
        "/api/v1/taxes/preview",
        data=json.dumps({"shipping_price": 50000}),
        content_type="application/json",
        HTTP_HOST="tax.local",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["tax"] == "90000"
    assert data["payable_total"] == "1140000"


@pytest.mark.django_db
def test_tax_rules_crud_api(client, store, admin_headers):
    response = client.post(
        "/api/v1/store-admin/taxes/rules",
        data=json.dumps({
            "name": "Luxury",
            "rate_percent": 15,
            "scope": "all",
            "priority": 1,
        }),
        content_type="application/json",
        **admin_headers,
    )
    assert response.status_code == 200
    rule_id = response.json()["id"]

    response = client.get("/api/v1/store-admin/taxes/rules", **admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.put(
        f"/api/v1/store-admin/taxes/rules/{rule_id}",
        data=json.dumps({"rate_percent": 12}),
        content_type="application/json",
        **admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["rate_percent"] == "12.0"


@pytest.mark.django_db
def test_payment_includes_tax(client, store, user, cart_with_item, admin_headers):
    from addresses.models import CustomerAddress
    from payments.models import PaymentTransaction
    from shipping.enums import CalculationMode, ShippingProviderType
    from shipping.models import ShippingMethod, ShippingZone
    from tenants.models import StoreSetting

    StoreSetting.objects.create(store=store, group="payment", key="gateways", value=["zarinpal"])
    StoreSetting.objects.create(store=store, group="payment", key="zarinpal", value={"merchant_id": "x", "sandbox": True})

    zone = ShippingZone.objects.create(store=store, name="All")
    method = ShippingMethod.objects.create(
        store=store, zone=zone, name="Post", slug="post",
        provider=ShippingProviderType.POST, calculation_mode=CalculationMode.FIXED,
        config={"fixed_price": 50000},
    )
    CustomerAddress.objects.create(
        user=user, store=store, full_name="U", phone="09125556677",
        province="Tehran", city="Tehran", postal_code="1234567890", address_line="X",
    )

    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    headers = {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "tax.local"}

    response = client.post(
        "/api/v1/payments/create",
        data=json.dumps({
            "gateway": "zarinpal",
            "address_id": 1,
            "shipping_method_id": method.id,
            "shipping_price": 50000,
        }),
        content_type="application/json",
        **headers,
    )
    assert response.status_code == 200
    assert response.json()["amount"] == "1140000"

    txn = PaymentTransaction.objects.get()
    assert txn.metadata["tax"] == "90000"
