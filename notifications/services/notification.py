"""Notification dispatch service."""

import logging

from django.utils import timezone

from notifications.enums import ChannelType, NotificationStatus
from notifications.models import NotificationChannel, NotificationLog
from notifications.providers.registry import get_provider, list_providers

logger = logging.getLogger(__name__)

DEFAULT_PROVIDERS = {
    ChannelType.SMS: "console_sms",
    ChannelType.EMAIL: "console_email",
    ChannelType.PUSH: "console_push",
    ChannelType.WEBHOOK: "webhook",
    ChannelType.TELEGRAM: "telegram",
}


class NotificationError(Exception):
    pass


class NotificationService:
    """Send notifications via configured channel drivers."""

    def list_providers(self, channel_type: str | None = None) -> list[dict]:
        return [
            {"codename": p.codename, "label": p.label, "channel_type": p.channel_type}
            for p in list_providers(channel_type)
        ]

    def get_channel(self, store, channel_type: str) -> tuple[object, dict]:
        qs = NotificationChannel.objects.filter(
            store=store,
            channel_type=channel_type,
            is_active=True,
        ).order_by("-is_default", "id")

        channel = qs.first()
        if channel:
            provider = get_provider(channel.provider)
            if provider:
                return provider, channel.config

        codename = DEFAULT_PROVIDERS.get(channel_type, "console_sms")
        provider = get_provider(codename)
        if not provider:
            raise NotificationError("ارائه‌دهنده اعلان یافت نشد")
        return provider, {}

    def send(
        self,
        channel_type: str,
        recipient: str,
        body: str,
        store=None,
        subject: str = "",
        metadata: dict | None = None,
    ) -> NotificationLog:
        provider, config = self.get_channel(store, channel_type) if store else self._platform_channel(channel_type)

        log = NotificationLog.objects.create(
            store=store,
            channel_type=channel_type,
            provider=provider.codename,
            recipient=recipient,
            subject=subject,
            body=body,
            metadata=metadata or {},
        )

        try:
            result = provider.send(recipient, body, config, subject=subject)
            if result.success:
                log.status = NotificationStatus.SENT
                log.sent_at = timezone.now()
                log.metadata = {**(log.metadata or {}), "result": result.message, "external_id": result.external_id}
            else:
                log.status = NotificationStatus.FAILED
                log.error_message = result.message
            log.save()
            if not result.success:
                raise NotificationError(result.message)
            return log
        except Exception as exc:
            log.status = NotificationStatus.FAILED
            log.error_message = str(exc)
            log.save()
            logger.exception("Notification failed: %s", channel_type)
            raise NotificationError(str(exc)) from exc

    def send_sms(self, phone: str, message: str, store=None, metadata: dict | None = None) -> NotificationLog:
        return self.send(ChannelType.SMS, phone, message, store=store, metadata=metadata)

    def send_email(self, email: str, subject: str, body: str, store=None) -> NotificationLog:
        return self.send(ChannelType.EMAIL, email, body, store=store, subject=subject)

    def send_otp_sms(self, phone: str, code: str, store=None) -> NotificationLog:
        message = f"کد ورود ShopCMS: {code}\nاعتبار: ۲ دقیقه"
        return self.send_sms(phone, message, store=store, metadata={"purpose": "otp"})

    def list_logs(self, store, channel_type: str | None = None, limit: int = 50):
        qs = NotificationLog.objects.filter(store=store)
        if channel_type:
            qs = qs.filter(channel_type=channel_type)
        return qs[:limit]

    def serialize_log(self, log: NotificationLog) -> dict:
        return {
            "id": log.id,
            "channel_type": log.channel_type,
            "provider": log.provider,
            "recipient": log.recipient,
            "subject": log.subject,
            "body": log.body[:200],
            "status": log.status,
            "error_message": log.error_message,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            "created_at": log.created_at.isoformat(),
        }

    def _platform_channel(self, channel_type: str):
        codename = DEFAULT_PROVIDERS.get(channel_type, "console_sms")
        provider = get_provider(codename)
        if not provider:
            raise NotificationError("ارائه‌دهنده اعلان یافت نشد")
        return provider, {}
