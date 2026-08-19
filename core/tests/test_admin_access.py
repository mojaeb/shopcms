"""Django admin is superuser-only."""

import pytest
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
def test_staff_user_cannot_open_admin_or_docs(client):
    staff = User.objects.create_user(phone="09121110000", is_staff=True, password="x")
    client.force_login(staff)

    index = client.get("/admin/")
    assert index.status_code == 302
    assert "/admin/login/" in index.headers.get("Location", "")

    docs = client.get(reverse("admin:shopcms_docs"))
    assert docs.status_code == 302
    assert "/admin/login/" in docs.headers.get("Location", "")


@pytest.mark.django_db
def test_superuser_can_open_admin(client):
    user = User.objects.create_superuser(phone="09121110001", password="x")
    client.force_login(user)
    response = client.get("/admin/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_staff_cannot_login_to_admin(client):
    User.objects.create_user(phone="09121110002", is_staff=True, password="secret12")
    response = client.post(
        "/admin/login/",
        {"username": "09121110002", "password": "secret12", "next": "/admin/"},
    )
    assert response.status_code == 200
    assert response.context["form"].errors
