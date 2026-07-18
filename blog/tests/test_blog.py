"""Blog tests."""

import json

import pytest
from django.utils import timezone

from accounts.enums import RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from blog.models import BlogCategory, BlogPost, BlogTag
from blog.services.blog import BlogError, BlogService
from comments.enums import CommentStatus
from tenants.models import Domain, Plugin, Store, StorePlugin, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Blog Shop", slug="blog-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="blog.local")
    plugin, _ = Plugin.objects.get_or_create(codename="blog", defaults={"name": "Blog", "is_active": True})
    StorePlugin.objects.create(store=s, plugin=plugin, is_enabled=True)
    return s


@pytest.fixture
def user(db):
    return User.objects.create_user(phone="09126667799", phone_verified=True, first_name="Writer")


@pytest.fixture
def content_role(db):
    role = Role.objects.create(codename="content", name="Content", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="blog.manage", name="Blog", group="content")
    role.permissions.add(perm)
    return role


@pytest.fixture
def staff_user(db, store, content_role):
    u = User.objects.create_user(phone="09125554433", phone_verified=True)
    StoreMembership.objects.create(user=u, store=store, role=content_role)
    return u


@pytest.fixture
def category(store):
    return BlogCategory.objects.create(store=store, name="News", slug="news", is_active=True)


@pytest.fixture
def published_post(store, user, category):
    return BlogPost.objects.create(
        store=store, title="Hello", slug="hello", content="Body", excerpt="Excerpt",
        category=category, author=user, is_published=True, published_at=timezone.now(),
        meta_title="Hello SEO", meta_description="Desc",
    )


@pytest.fixture
def auth_headers(user, store):
    token = JWTService().create_tokens(user.id, store.id, "customer", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "blog.local"}


@pytest.fixture
def staff_headers(staff_user, store):
    token = JWTService().create_tokens(staff_user.id, store.id, "content", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "blog.local"}


@pytest.mark.django_db
def test_list_published_posts(store, published_post):
    posts = BlogService().list_published_posts(store)
    assert posts.count() == 1


@pytest.mark.django_db
def test_post_detail_includes_seo(store, published_post):
    post = BlogService().get_post(store, "hello")
    data = BlogService().serialize_post_detail(post)
    assert data["seo"]["meta_title"] == "Hello SEO"


@pytest.mark.django_db
def test_blog_comment_flow(store, user, published_post, auth_headers):
    service = BlogService()
    comment = service.create_comment(user, store, "hello", "Nice post")
    assert comment.status == CommentStatus.PENDING
    service.moderate_comment(store, comment.id, CommentStatus.APPROVED)
    comments = service.list_post_comments(store, "hello")
    assert comments.count() == 1


@pytest.mark.django_db
def test_public_posts_api(client, store, published_post):
    response = client.get("/api/v1/blog/posts", HTTP_HOST="blog.local")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["items"][0]["slug"] == "hello"


@pytest.mark.django_db
def test_post_detail_api(client, store, published_post):
    response = client.get("/api/v1/blog/posts/hello", HTTP_HOST="blog.local")
    assert response.status_code == 200
    assert response.json()["content"] == "Body"


@pytest.mark.django_db
def test_admin_create_post(client, store, staff_headers, category):
    response = client.post(
        "/api/v1/store-admin/blog/posts",
        data=json.dumps({
            "title": "New Post",
            "slug": "new-post",
            "content": "Content here",
            "category_id": category.id,
            "is_published": True,
            "meta_title": "SEO Title",
        }),
        content_type="application/json",
        **staff_headers,
    )
    assert response.status_code == 200
    assert BlogPost.objects.filter(slug="new-post").exists()


@pytest.mark.django_db
def test_storefront_blog_pages(client, store, published_post):
    response = client.get("/blog/", HTTP_HOST="blog.local")
    assert response.status_code == 200
    assert "blog-list-page" in response.content.decode()

    response = client.get("/blog/hello/", HTTP_HOST="blog.local")
    assert response.status_code == 200
    assert "blog-single-page" in response.content.decode()
