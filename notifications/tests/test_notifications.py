"""Notification tests."""

import pytest

from notifications.enums import ChannelType, NotificationStatus
from notifications.models import NotificationChannel, NotificationLog
from notifications.services.notification import NotificationService
from tenants.models import Domain, Store, Theme


@pytest.fixture
def store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    s = Store.objects.create(name="Notify Shop", slug="notify-shop", default_theme=theme, status="active")
    Domain.objects.create(store=s, domain="notify.local")
    return s


@pytest.mark.django_db
def test_list_providers():
    providers = NotificationService().list_providers(ChannelType.SMS)
    codenames = {p["codename"] for p in providers}
    assert "console_sms" in codenames
    assert "payamak" in codenames


@pytest.mark.django_db
def test_send_sms_creates_log(store):
    service = NotificationService()
    NotificationChannel.objects.create(
        store=store,
        channel_type=ChannelType.SMS,
        provider="console_sms",
        is_default=True,
        is_active=True,
    )
    log = service.send_sms("09120001111", "Hello", store=store)
    assert log.status == NotificationStatus.SENT
    assert NotificationLog.objects.filter(store=store, recipient="09120001111").exists()


@pytest.mark.django_db
def test_send_otp_sms(store):
    log = NotificationService().send_otp_sms("09123334444", "12345", store=store)
    assert log.status == NotificationStatus.SENT
    assert "12345" in log.body


@pytest.mark.django_db
def test_send_otp_sms_uses_channel_template(store):
    NotificationChannel.objects.create(
        store=store,
        channel_type=ChannelType.SMS,
        provider="console_sms",
        is_default=True,
        is_active=True,
        config={"otp_template": "کد شما {code}"},
    )
    log = NotificationService().send_otp_sms("09123334444", "99887", store=store)
    assert log.body == "کد شما 99887"


@pytest.mark.django_db
def test_payamak_otp_posts_pattern_api(store, monkeypatch):
    from notifications.providers.payamak import PayamakSmsProvider

    captured = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"RetStatus":1,"Value":"rec-1","StrRetStatus":"Ok"}'

        status = 200

    def fake_urlopen(req, timeout=15):
        captured["url"] = req.full_url
        captured["body"] = req.data.decode("utf-8")
        return _Resp()

    monkeypatch.setattr("notifications.providers.payamak.urllib.request.urlopen", fake_urlopen)
    NotificationChannel.objects.create(
        store=store,
        channel_type=ChannelType.SMS,
        provider="payamak",
        is_default=True,
        is_active=True,
        config={"username": "user1", "password": "secret", "body_id": "226930"},
    )
    log = NotificationService().send_otp_sms("09123334444", "123456", store=store)
    assert log.status == NotificationStatus.SENT
    assert "BaseServiceNumber" in captured["url"]
    assert "bodyId=226930" in captured["body"]
    assert "text=123456" in captured["body"]
    assert "to=09123334444" in captured["body"]
    assert PayamakSmsProvider.codename == "payamak"


@pytest.mark.django_db
def test_otp_uses_notification_service(setup_store):
    from accounts.enums import OTPPurpose
    from accounts.models import OTPCode
    from accounts.services.otp import OTPService

    OTPService().send_otp("09125556677", OTPPurpose.REGISTER, store=setup_store)
    assert NotificationLog.objects.filter(recipient="09125556677", channel_type=ChannelType.SMS).exists()
    assert OTPCode.objects.filter(phone="09125556677").exists()


@pytest.fixture
def setup_store(db):
    theme = Theme.objects.create(name="Default", slug="default", directory="default", is_default=True)
    store = Store.objects.create(name="Shop One", slug="shop1", default_theme=theme, status="active")
    Domain.objects.create(store=store, domain="localhost", is_primary=True)
    return store
