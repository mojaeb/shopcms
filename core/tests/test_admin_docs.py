"""Admin documentation hub smoke tests."""

import pytest
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
def test_docs_index_and_json_templates_require_staff(client):
    index_url = reverse("admin:shopcms_docs")
    page_url = reverse("admin:shopcms_docs_page", kwargs={"slug": "json-templates"})

    assert client.get(index_url).status_code == 302

    user = User.objects.create_superuser(phone="09121112233", password="x")
    client.force_login(user)

    index = client.get(index_url)
    assert index.status_code == 200
    assert "مستندات".encode("utf-8") in index.content
    assert b"json-templates" in index.content

    page = client.get(page_url)
    assert page.status_code == 200
    assert "کتابخانه قالب".encode("utf-8") in page.content or b"JSON" in page.content


@pytest.mark.django_db
def test_docs_unknown_slug_404(client):
    user = User.objects.create_superuser(phone="09121112234", password="x")
    client.force_login(user)
    url = reverse("admin:shopcms_docs_page", kwargs={"slug": "no-such-doc"})
    assert client.get(url).status_code == 404
