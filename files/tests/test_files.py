"""Files tests."""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from accounts.enums import RoleScope
from accounts.models import Permission, Role, StoreMembership, User
from accounts.services.jwt import JWTService
from files.enums import FileType
from files.services.file import FileError, FileService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Files Shop", slug="files-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="files.local")
    return s


@pytest.fixture
def staff_role(db):
    role = Role.objects.create(codename="content", name="Content", scope=RoleScope.STORE)
    perm = Permission.objects.create(codename="files.manage", name="Manage Files", group="content")
    role.permissions.add(perm)
    return role


@pytest.fixture
def staff_user(db, store, staff_role):
    user = User.objects.create_user(phone="09124443322", phone_verified=True)
    StoreMembership.objects.create(user=user, store=store, role=staff_role)
    return user


@pytest.fixture
def staff_headers(staff_user, store):
    token = JWTService().create_tokens(staff_user.id, store.id, "content", 1).access_token
    return {"HTTP_AUTHORIZATION": f"Bearer {token}", "HTTP_HOST": "files.local"}


def _make_image(name="photo.jpg", size=(400, 300), color=(200, 50, 50)):
    buffer = BytesIO()
    Image.new("RGB", size, color=color).save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


def _make_video(name="clip.mp4"):
    return SimpleUploadedFile(name, b"fake-video-content", content_type="video/mp4")


@pytest.mark.django_db
def test_detect_file_types():
    service = FileService()
    assert service.detect_file_type("a.jpg") == FileType.IMAGE
    assert service.detect_file_type("b.mp4") == FileType.VIDEO
    assert service.detect_file_type("c.pdf") == FileType.DOCUMENT


@pytest.mark.django_db
def test_upload_image_creates_thumbnails(store):
    service = FileService()
    media = service.upload(store, _make_image(), folder="products")
    assert media.file_type == FileType.IMAGE
    assert media.folder == "products"
    assert media.width == 400
    assert media.height == 300
    assert media.thumbnails.count() == 4


@pytest.mark.django_db
def test_upload_video(store):
    service = FileService()
    media = service.upload(store, _make_video())
    assert media.file_type == FileType.VIDEO
    assert media.thumbnails.count() == 0


@pytest.mark.django_db
def test_delete_file_removes_records(store):
    service = FileService()
    media = service.upload(store, _make_image())
    file_id = media.id
    service.delete_file(store, file_id)
    with pytest.raises(FileError):
        service.get_file(store, file_id)


@pytest.mark.django_db
def test_reject_oversized_file(store, settings):
    settings.FILE_UPLOAD_MAX_SIZE = 10
    service = FileService()
    with pytest.raises(FileError):
        service.upload(store, _make_image())


@pytest.mark.django_db
def test_list_storage_drivers_api(client, staff_headers):
    response = client.get("/api/v1/store-admin/files/drivers", **staff_headers)
    assert response.status_code == 200
    data = response.json()
    codenames = {item["codename"] for item in data}
    assert "local" in codenames
    assert "s3" in codenames


@pytest.mark.django_db
def test_upload_and_list_api(client, staff_headers):
    image = _make_image()
    response = client.post(
        "/api/v1/store-admin/files/upload",
        {"file": image, "folder": "catalog", "title": "Hero"},
        **staff_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["file_type"] == FileType.IMAGE
    assert payload["folder"] == "catalog"
    assert len(payload["thumbnails"]) == 4

    list_response = client.get("/api/v1/store-admin/files?file_type=image", **staff_headers)
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Hero"


@pytest.mark.django_db
def test_delete_file_api(client, staff_headers, store):
    service = FileService()
    media = service.upload(store, _make_image())
    response = client.delete(f"/api/v1/store-admin/files/{media.id}", **staff_headers)
    assert response.status_code == 200
