"""Concrete notification providers."""

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail import send_mail

from notifications.enums import ChannelType
from notifications.providers.base import NotificationProvider, SendResult
from notifications.providers.registry import register
from notifications.providers.payamak import PayamakSmsProvider  # noqa: F401

logger = logging.getLogger(__name__)


@register
class ConsoleSmsProvider(NotificationProvider):
    codename = "console_sms"
    label = "Console SMS"
    channel_type = ChannelType.SMS

    def send(self, recipient: str, body: str, config: dict, subject: str = "", metadata: dict | None = None) -> SendResult:
        logger.info("SMS to %s: %s", recipient, body)
        return SendResult(success=True, message="logged", external_id="console")


@register
class KavenegarSmsProvider(NotificationProvider):
    codename = "kavenegar"
    label = "Kavenegar"
    channel_type = ChannelType.SMS

    def validate_config(self, config: dict) -> None:
        if not config.get("api_key"):
            raise ValueError("api_key is required")

    def send(self, recipient: str, body: str, config: dict, subject: str = "", metadata: dict | None = None) -> SendResult:
        raise RuntimeError("Kavenegar driver requires HTTP integration and store config")


@register
class ConsoleEmailProvider(NotificationProvider):
    codename = "console_email"
    label = "Console Email"
    channel_type = ChannelType.EMAIL

    def send(self, recipient: str, body: str, config: dict, subject: str = "", metadata: dict | None = None) -> SendResult:
        logger.info("Email to %s [%s]: %s", recipient, subject, body)
        return SendResult(success=True, message="logged", external_id="console")


@register
class SmtpEmailProvider(NotificationProvider):
    codename = "smtp"
    label = "SMTP"
    channel_type = ChannelType.EMAIL

    def send(self, recipient: str, body: str, config: dict, subject: str = "", metadata: dict | None = None) -> SendResult:
        from_email = config.get("from_email") or getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@shopcms.local")
        try:
            send_mail(subject or "ShopCMS", body, from_email, [recipient], fail_silently=False)
            return SendResult(success=True, message="sent")
        except Exception as exc:
            return SendResult(success=False, message=str(exc))


@register
class WebhookProvider(NotificationProvider):
    codename = "webhook"
    label = "Webhook"
    channel_type = ChannelType.WEBHOOK

    def validate_config(self, config: dict) -> None:
        if not config.get("url"):
            raise ValueError("url is required")

    def send(self, recipient: str, body: str, config: dict, subject: str = "", metadata: dict | None = None) -> SendResult:
        payload = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "metadata": metadata or config.get("metadata", {}),
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            config["url"],
            data=data,
            headers={"Content-Type": "application/json", **config.get("headers", {})},
            method=config.get("method", "POST"),
        )
        try:
            with urllib.request.urlopen(req, timeout=config.get("timeout", 10)) as response:
                return SendResult(success=True, message="delivered", raw={"status": response.status})
        except urllib.error.URLError as exc:
            return SendResult(success=False, message=str(exc))


@register
class ConsolePushProvider(NotificationProvider):
    codename = "console_push"
    label = "Console Push"
    channel_type = ChannelType.PUSH

    def send(self, recipient: str, body: str, config: dict, subject: str = "", metadata: dict | None = None) -> SendResult:
        logger.info("Push to %s [%s]: %s", recipient, subject, body)
        return SendResult(success=True, message="logged", external_id="console")


@register
class TelegramProvider(NotificationProvider):
    codename = "telegram"
    label = "Telegram"
    channel_type = ChannelType.TELEGRAM

    def validate_config(self, config: dict) -> None:
        if not config.get("bot_token"):
            raise ValueError("bot_token is required")

    def send(self, recipient: str, body: str, config: dict, subject: str = "", metadata: dict | None = None) -> SendResult:
        raise RuntimeError("Telegram driver requires HTTP integration and store config")
