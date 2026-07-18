"""Comment tests."""

import json

import pytest

from accounts.enums import RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from comments.enums import CommentStatus
from comments.models import Comment, CommentLike
from comments.services.comment import CommentError, CommentService
from orders.enums import OrderStatus
from orders.models import Order, OrderItem
from products.enums import ProductStatus, ProductType
from products.models import Inventory, Product
from tenants.models import Domain, Plugin, Store, StorePlugin, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Comment Shop", slug="comment-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="comment.local")
    plugin, _ = Plugin.objects.get_or_create(codename="comments", defaults={"name": "Comments", "is_active": True})
    StorePlugin.objects.create(store=s, plugin=plugin, is_enabled=True)
    return s


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="09124443322", phone_verified=True, first_name="Ali")


@pytest.fixture
def moderator_role(db):
    role = Role.objects.create(codename="content", name="Content", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="comments.moderate", name="Moderate", group="content")
    role.permissions.add(perm)
    return role


@pytest.fixture
def moderator(db, store, moderator_role):
    u = User.objects.create_user(phone="09121112244", phone_verified=True)
    StoreMembership.objects.create(user=u, store=store, role=moderator_role)
    return u


@pytest.fixture
def product(store):
    p = Product.objects.create(
        store=store, name="Comment Product", slug="comment-product",
        status=ProductStatus.ACTIVE, base_price=600000, product_type=ProductType.SIMPLE,
    )
    Inventory.objects.create(product=p, quantity=5)
    return p


@pytest.fixture
def auth_headers(user, store):
    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "comment.local"}


@pytest.fixture
def mod_headers(moderator, store):
    token = JWTService().create_tokens(moderator.id, store.id, "content", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "comment.local"}


@pytest.mark.django_db
def test_create_comment_pending(store, user, product):
    service = CommentService()
    comment = service.create_comment(user, store, "comment-product", "Great product", 5)
    assert comment.status == CommentStatus.PENDING
    assert comment.rating == 5


@pytest.mark.django_db
def test_approved_comments_visible(store, user, product):
    service = CommentService()
    comment = service.create_comment(user, store, "comment-product", "Nice", 4)
    service.moderate_comment(store, comment.id, CommentStatus.APPROVED)
    items = service.list_product_comments(store, "comment-product")
    assert items.count() == 1


@pytest.mark.django_db
def test_reply_comment(store, user, product):
    service = CommentService()
    parent = service.create_comment(user, store, "comment-product", "Question?", 5)
    service.moderate_comment(store, parent.id, CommentStatus.APPROVED)
    reply = service.create_comment(user, store, "comment-product", "Thanks", parent_id=parent.id)
    assert reply.parent_id == parent.id
    assert reply.rating is None


@pytest.mark.django_db
def test_toggle_like(store, user, product):
    service = CommentService()
    comment = service.create_comment(user, store, "comment-product", "Like me", 5)
    service.moderate_comment(store, comment.id, CommentStatus.APPROVED)
    result = service.toggle_like(user, store, comment.id)
    assert result["liked"] is True
    assert CommentLike.objects.filter(comment=comment, user=user).exists()


@pytest.mark.django_db
def test_verified_purchase_badge(store, user, product):
    order = Order.objects.create(
        store=store, user=user, order_number="ORD-C1", status=OrderStatus.PAID, total=600000,
    )
    OrderItem.objects.create(
        order=order, product_id=product.id, product_name=product.name,
        quantity=1, unit_price=600000, line_total=600000,
    )
    comment = CommentService().create_comment(user, store, "comment-product", "Verified", 5)
    assert comment.is_verified_purchase is True


@pytest.mark.django_db
def test_comment_api(client, store, user, auth_headers, product):
    response = client.post(
        "/api/v1/comments/",
        data=json.dumps({"product_slug": "comment-product", "body": "API review", "rating": 5}),
        content_type="application/json",
        **auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == CommentStatus.PENDING


@pytest.mark.django_db
def test_moderation_api(client, store, user, auth_headers, mod_headers, product):
    service = CommentService()
    comment = service.create_comment(user, store, "comment-product", "Mod me", 3)

    response = client.put(
        f"/api/v1/store-admin/comments/{comment.id}/status",
        data=json.dumps({"status": CommentStatus.APPROVED}),
        content_type="application/json",
        **mod_headers,
    )
    assert response.status_code == 200
    comment.refresh_from_db()
    assert comment.status == CommentStatus.APPROVED


@pytest.mark.django_db
def test_storefront_comments_page(client, store):
    response = client.get("/comments/", HTTP_HOST="comment.local")
    assert response.status_code == 200
    assert "my-comments-page" in response.content.decode()
