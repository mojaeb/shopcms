"""Shipping tests."""

import json
from decimal import Decimal

import pytest

from carts.models import Cart, CartItem
from products.enums import ProductStatus, ProductType
from products.models import Inventory, Product
from shipping.data.province_adjacency import zone_tier
from shipping.enums import CalculationMode, ShippingPaymentType, ShippingProviderType
from shipping.models import ShippingMethod, ShippingPrice, ShippingZone
from shipping.services.shipping import ShippingService
from tenants.models import Domain, Store, StoreSetting, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Ship Shop", slug="ship-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="ship.local")
    return s


@pytest.fixture
def shipping_setup(store):
    zone = ShippingZone.objects.create(store=store, name="All", is_active=True)
    fixed = ShippingMethod.objects.create(
        store=store, zone=zone, name="Post Fixed", slug="post-fixed",
        provider=ShippingProviderType.POST, calculation_mode=CalculationMode.FIXED,
        config={"fixed_price": 50000}, is_active=True,
    )
    distance = ShippingMethod.objects.create(
        store=store, zone=zone, name="Tipax", slug="tipax",
        provider=ShippingProviderType.TIPAX, calculation_mode=CalculationMode.DISTANCE,
        config={"origin_city": "مشهد", "fixed_price": 100000}, is_active=True,
    )
    ShippingPrice.objects.create(method=distance, from_city="مشهد", to_city="تهران", price=180000)
    weight_method = ShippingMethod.objects.create(
        store=store, zone=zone, name="Weight", slug="weight",
        provider=ShippingProviderType.POST, calculation_mode=CalculationMode.WEIGHT,
        config={"fixed_price": 90000}, is_active=True,
    )
    ShippingPrice.objects.create(method=weight_method, weight_min_kg=0, weight_max_kg=2, price=70000)
    ShippingPrice.objects.create(method=weight_method, weight_min_kg=2, weight_max_kg=5, price=120000)
    return {"fixed": fixed, "distance": distance, "weight": weight_method}


@pytest.fixture
def cart_with_items(store):
    product = Product.objects.create(
        store=store, name="Item", slug="item", status=ProductStatus.ACTIVE,
        base_price=1000000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=product, quantity=10)
    cart = Cart.objects.create(store=store, session_key="ship-test")
    CartItem.objects.create(cart=cart, product=product, quantity=2, unit_price=1000000)
    return cart


@pytest.mark.django_db
def test_fixed_shipping_quote(store, shipping_setup):
    service = ShippingService()
    quotes = service.get_quotes(store, "تهران", "تهران")
    fixed_quote = next(q for q in quotes if q.slug == "post-fixed")
    assert fixed_quote.price == Decimal("50000")


@pytest.mark.django_db
def test_distance_shipping_quote(store, shipping_setup):
    service = ShippingService()
    quotes = service.get_quotes(store, "تهران", "تهران")
    tipax = next(q for q in quotes if q.slug == "tipax")
    assert tipax.price == Decimal("180000")


@pytest.mark.django_db
def test_weight_shipping_quote(store, shipping_setup, cart_with_items):
    service = ShippingService()
    context = service.build_context(store, "تهران", "تهران", cart=cart_with_items)
    assert context.weight_kg == Decimal("1.0")
    quotes = service.get_quotes(store, "تهران", "تهران", cart=cart_with_items)
    weight_q = next(q for q in quotes if q.slug == "weight")
    assert weight_q.price == Decimal("70000")


@pytest.mark.django_db
def test_shipping_calculate_api(client, store, shipping_setup, cart_with_items):
    session = client.session
    session.save()
    cart_with_items.session_key = session.session_key
    cart_with_items.save()

    response = client.post(
        "/api/v1/shipping/calculate",
        data=json.dumps({"province": "تهران", "city": "تهران"}),
        content_type="application/json",
        HTTP_HOST="ship.local",
    )
    assert response.status_code == 200
    assert len(response.json()["quotes"]) >= 2


@pytest.mark.django_db
def test_shipping_methods_api(client, store, shipping_setup):
    response = client.get("/api/v1/shipping/methods", HTTP_HOST="ship.local")
    assert response.status_code == 200
    assert len(response.json()) >= 3


@pytest.mark.django_db
def test_storefront_checkout_page(client, store):
    response = client.get("/checkout/", HTTP_HOST="ship.local")
    assert response.status_code == 302
    assert response["Location"].startswith("/login/?next=")
    assert "/checkout/" in response["Location"]


@pytest.mark.django_db
def test_storefront_checkout_page_authenticated(client, store):
    from accounts.models import User

    user = User.objects.create_user(phone="09125556677", phone_verified=True)
    client.force_login(user)
    response = client.get("/checkout/", HTTP_HOST="ship.local")
    assert response.status_code == 200
    assert "checkout-page" in response.content.decode()


@pytest.mark.django_db
def test_build_context_uses_product_weight(store, cart_with_items):
    product = cart_with_items.items.first().product
    product.weight_kg = Decimal("2.000")
    product.save(update_fields=["weight_kg"])
    context = ShippingService().build_context(store, "تهران", "تهران", cart=cart_with_items)
    # qty 2 × 2.0kg; no package-weight setting → 4.0
    assert context.weight_kg == Decimal("4.000")


@pytest.mark.django_db
def test_build_context_uses_variant_weight(store):
    from products.models import ProductVariant

    product = Product.objects.create(
        store=store, name="Var", slug="var", status=ProductStatus.ACTIVE,
        base_price=100000, product_type=ProductType.VARIABLE, weight_kg=Decimal("0.5"),
    )
    variant = ProductVariant.objects.create(product=product, price=100000, weight_kg=Decimal("3.000"))
    Inventory.objects.create(product=product, quantity=10)
    cart = Cart.objects.create(store=store, session_key="ship-var")
    CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=1, unit_price=100000)
    context = ShippingService().build_context(store, "تهران", "تهران", cart=cart)
    assert context.weight_kg == Decimal("3.000")


@pytest.mark.django_db
def test_build_context_adds_package_weight(store, cart_with_items):
    StoreSetting.objects.create(store=store, group="shipping", key="base_package_weight_kg", value=0.1)
    context = ShippingService().build_context(store, "تهران", "تهران", cart=cart_with_items)
    assert context.weight_kg == Decimal("1.1")


@pytest.mark.django_db
def test_zone_tier_helper():
    assert zone_tier("خراسان رضوی", "خراسان رضوی") == "same"
    assert zone_tier("خراسان رضوی", "سمنان") == "adjacent"
    assert zone_tier("خراسان رضوی", "فارس") == "far"


@pytest.mark.django_db
def test_zone_tier_adjacent_price(store, shipping_setup):
    method = shipping_setup["distance"]
    ShippingPrice.objects.create(
        method=method, from_city="", to_city="", zone_tier="adjacent", price=90000,
    )
    quotes = ShippingService().get_quotes(store, "سمنان", "سمنان")
    tipax = next(q for q in quotes if q.slug == "tipax")
    assert tipax.price == Decimal("90000")


@pytest.mark.django_db
def test_zone_tier_far_price(store, shipping_setup):
    method = shipping_setup["distance"]
    ShippingPrice.objects.create(
        method=method, from_city="", to_city="", zone_tier="far", price=250000,
    )
    quotes = ShippingService().get_quotes(store, "فارس", "شیراز")
    tipax = next(q for q in quotes if q.slug == "tipax")
    assert tipax.price == Decimal("250000")


@pytest.mark.django_db
def test_city_row_beats_zone_tier(store, shipping_setup):
    method = shipping_setup["distance"]
    ShippingPrice.objects.create(
        method=method, from_city="", to_city="", zone_tier="far", price=50000,
    )
    quotes = ShippingService().get_quotes(store, "تهران", "تهران")
    tipax = next(q for q in quotes if q.slug == "tipax")
    assert tipax.price == Decimal("180000")


@pytest.mark.django_db
def test_peyk_delivery_cities_filter(store):
    zone = ShippingZone.objects.create(store=store, name="All", is_active=True)
    ShippingMethod.objects.create(
        store=store, zone=zone, name="Peyk", slug="peyk-tehran",
        provider=ShippingProviderType.PEYK, calculation_mode=CalculationMode.FIXED,
        config={"fixed_price": 40000, "delivery_cities": ["تهران"]},
        is_active=True,
    )
    service = ShippingService()
    in_quotes = service.get_quotes(store, "تهران", "تهران")
    assert any(q.slug == "peyk-tehran" for q in in_quotes)
    out_quotes = service.get_quotes(store, "خراسان رضوی", "مشهد")
    assert all(q.slug != "peyk-tehran" for q in out_quotes)


@pytest.mark.django_db
def test_postpaid_quote_label_and_serialize(store):
    zone = ShippingZone.objects.create(store=store, name="All", is_active=True)
    ShippingMethod.objects.create(
        store=store, zone=zone, name="پست", slug="post-cod",
        provider=ShippingProviderType.POST, calculation_mode=CalculationMode.FIXED,
        config={"fixed_price": 80000}, is_active=True,
        payment_type=ShippingPaymentType.POSTPAID,
    )
    service = ShippingService()
    quote = next(q for q in service.get_quotes(store, "تهران", "تهران") if q.slug == "post-cod")
    assert quote.payment_type == "postpaid"
    assert quote.name.endswith("پس‌کرایه")
    serialized = service.serialize_quote(quote)
    assert serialized["payment_type"] == "postpaid"
    assert "پس‌کرایه" in serialized["name"]


@pytest.mark.django_db
def test_extra_cost_flat_and_percent(store):
    zone = ShippingZone.objects.create(store=store, name="All", is_active=True)
    ShippingMethod.objects.create(
        store=store, zone=zone, name="Extra", slug="extra",
        provider=ShippingProviderType.POST, calculation_mode=CalculationMode.FIXED,
        config={"fixed_price": 100000, "extra_cost_flat": 5000, "extra_cost_percent": 10},
        is_active=True,
    )
    quote = next(q for q in ShippingService().get_quotes(store, "تهران", "تهران") if q.slug == "extra")
    assert quote.price == Decimal("115000")


@pytest.mark.django_db
def test_post_max_weight_hides_quote(store, cart_with_items):
    product = cart_with_items.items.first().product
    product.weight_kg = Decimal("20")
    product.save(update_fields=["weight_kg"])
    zone = ShippingZone.objects.create(store=store, name="All", is_active=True)
    ShippingMethod.objects.create(
        store=store, zone=zone, name="Post Light", slug="post-max",
        provider=ShippingProviderType.POST, calculation_mode=CalculationMode.FIXED,
        config={"fixed_price": 80000, "max_weight_kg": 30},
        is_active=True,
    )
    quotes = ShippingService().get_quotes(store, "تهران", "تهران", cart=cart_with_items)
    assert all(q.slug != "post-max" for q in quotes)
