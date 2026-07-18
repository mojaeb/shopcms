"""Device tracking tests."""

import pytest
from django.test import RequestFactory

from accounts.models import User
from accounts.services.device import DeviceService


@pytest.mark.django_db
def test_record_and_revoke_device():
    user = User.objects.create_user(phone="09127770000")
    factory = RequestFactory()
    request = factory.get("/", HTTP_USER_AGENT="pytest-agent", REMOTE_ADDR="127.0.0.1")
    service = DeviceService()

    device = service.record_login(request, user)
    assert device.user_id == user.id
    assert service.list_devices(user).count() == 1

    assert service.revoke_device(user, device.id) is True
    assert service.list_devices(user).count() == 0
