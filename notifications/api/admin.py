"""Store admin notifications API."""

from ninja import Router, Schema
from ninja.errors import HttpError

from dashboard.authentication_store import store_settings_auth
from notifications.enums import ChannelType
from notifications.models import NotificationChannel
from notifications.providers.registry import get_provider
from notifications.services.notification import NotificationError, NotificationService
from tenants.context import get_current_store

router = Router(auth=store_settings_auth)
service = NotificationService()


class ChannelCreateSchema(Schema):
    channel_type: str
    provider: str
    config: dict = {}
    is_default: bool = False
    is_active: bool = True


class TestSendSchema(Schema):
    channel_type: str
    recipient: str
    subject: str = ""
    body: str


def _store(request):
    store = get_current_store() or getattr(request, "store", None)
    if not store:
        raise HttpError(400, "فروشگاه مشخص نیست")
    return store


@router.get("/providers")
def list_providers(request, channel_type: str | None = None):
    return service.list_providers(channel_type)


@router.get("/channels")
def list_channels(request):
    store = _store(request)
    channels = NotificationChannel.objects.filter(store=store).order_by("channel_type")
    return [
        {
            "id": c.id,
            "channel_type": c.channel_type,
            "provider": c.provider,
            "config": c.config,
            "is_default": c.is_default,
            "is_active": c.is_active,
        }
        for c in channels
    ]


@router.post("/channels")
def create_channel(request, payload: ChannelCreateSchema):
    store = _store(request)
    if payload.channel_type not in ChannelType.values:
        raise HttpError(400, "نوع کانال نامعتبر است")
    provider = get_provider(payload.provider)
    if not provider:
        raise HttpError(400, "ارائه‌دهنده نامعتبر است")
    try:
        provider.validate_config(payload.config or {})
    except ValueError as exc:
        raise HttpError(400, str(exc)) from exc

    if payload.is_default:
        NotificationChannel.objects.filter(store=store, channel_type=payload.channel_type).update(is_default=False)

    channel, created = NotificationChannel.objects.update_or_create(
        store=store,
        channel_type=payload.channel_type,
        provider=payload.provider,
        defaults={
            "config": payload.config,
            "is_default": payload.is_default,
            "is_active": payload.is_active,
        },
    )
    return {"id": channel.id, "created": created}


@router.post("/test")
def test_send(request, payload: TestSendSchema):
    store = _store(request)
    if payload.channel_type not in ChannelType.values:
        raise HttpError(400, "نوع کانال نامعتبر است")
    try:
        log = service.send(
            payload.channel_type,
            payload.recipient,
            payload.body,
            store=store,
            subject=payload.subject,
        )
        return service.serialize_log(log)
    except NotificationError as exc:
        raise HttpError(400, str(exc))


@router.get("/logs")
def list_logs(request, channel_type: str | None = None):
    store = _store(request)
    logs = service.list_logs(store, channel_type=channel_type)
    return [service.serialize_log(log) for log in logs]
