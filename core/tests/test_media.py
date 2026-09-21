"""Media file serving (production must serve uploaded images)."""

from pathlib import Path

import pytest
from django.test import Client, override_settings


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_uploaded_media_is_served_when_debug_is_false(client, tmp_path):
    media_root = tmp_path / "media"
    rel = Path("stores/shop1/products/sample.jpg")
    dest = media_root / rel
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"\xff\xd8\xfffakejpeg")

    with override_settings(DEBUG=False, MEDIA_ROOT=media_root):
        response = client.get(f"/media/{rel.as_posix()}")

    assert response.status_code == 200
    body = b"".join(response.streaming_content)
    assert body.startswith(b"\xff\xd8\xff")
