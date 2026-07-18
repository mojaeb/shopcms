"""Plugin tests."""

import pytest

from accounts.enums import RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from plugins import events
from plugins.registry import get_plugin, list_codenames
from plugins.services.plugin import PluginError, PluginService
from tenants.enums import StoreType
from tenants.models import Domain, Plugin, Store, StorePlugin, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(
        name="Plugin Shop",
        slug="plugin-shop",
        default_theme=theme,
        status="active",
        store_type=StoreType.PHYSICAL,
    )
    Domain.objects.create(store=s, domain="plugin.local")
    return s


@pytest.fixture
def admin_user(db, store):
    role = Role.objects.create(codename="store_admin", name="Admin", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="settings.manage", name="Settings", group="settings")
    role.permissions.add(perm)
    user = User.objects.create_user(phone="09127778899", phone_verified=True, is_staff=True)
    StoreMembership.objects.create(user=user, store=store, role=role)
    return user


@pytest.fixture
def admin_headers(admin_user, store):
    token = JWTService().create_tokens(admin_user.id, store.id, "store_admin", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "plugin.local"}


@pytest.fixture(autouse=True)
def sync_plugins(db):
    PluginService().sync_registry_to_db()


@pytest.mark.django_db
def test_registry_lists_builtin_plugins():
    codenames = list_codenames()
    assert "physical" in codenames
    assert "digital_download" in codenames
    assert "booking" in codenames
    assert "blog" in codenames


@pytest.mark.django_db
def test_physical_plugin_manifest():
    plugin = get_plugin("physical")
    manifest = plugin.manifest()
    assert "api" in manifest.provides
    assert "settings" in manifest.provides


@pytest.mark.django_db
def test_install_defaults(store):
    PluginService().install_defaults(store)
    service = PluginService()
    assert service.is_enabled(store, "physical")
    assert service.is_enabled(store, "blog")
    assert not service.is_enabled(store, "digital_download")


@pytest.mark.django_db
def test_cannot_enable_incompatible_plugin(store):
    service = PluginService()
    service.install_defaults(store)
    with pytest.raises(PluginError):
        service.set_enabled(store, "digital_download", True)


@pytest.mark.django_db
def test_event_bus():
    events.clear_listeners()
    seen = []

    @events.on("order.created")
    def handler(**payload):
        seen.append(payload)

    events.emit("order.created", order_id=1)
    assert seen == [{"order_id": 1}]
    events.clear_listeners()


@pytest.mark.django_db
def test_list_plugins_api(client, admin_headers, store):
    PluginService().install_defaults(store)
    response = client.get("/api/v1/store-admin/plugins", **admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert any(item["codename"] == "physical" and item["is_enabled"] for item in data)


@pytest.mark.django_db
def test_toggle_plugin_api(client, admin_headers, store):
    PluginService().install_defaults(store)
    response = client.put(
        "/api/v1/store-admin/plugins/wishlist",
        data={"is_enabled": True, "settings": {}},
        content_type="application/json",
        **admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_enabled"] is True


@pytest.mark.django_db
def test_active_plugins_public_api(client, store):
    PluginService().install_defaults(store)
    response = client.get("/api/v1/plugins/active", HTTP_HOST="plugin.local")
    assert response.status_code == 200
    assert "physical" in response.json()["plugins"]


@pytest.mark.django_db
def test_plugin_info_api(client, store):
    PluginService().install_defaults(store)
    response = client.get("/api/v1/plugins/physical/info", HTTP_HOST="plugin.local")
    assert response.status_code == 200
    assert response.json()["codename"] == "physical"
