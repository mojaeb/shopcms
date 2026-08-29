"""Melipayamak / Payamak panel SMS (pattern + plain)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from accounts.managers import UserManager
from notifications.enums import ChannelType
from notifications.providers.base import NotificationProvider, SendResult
from notifications.providers.registry import register

logger = logging.getLogger(__name__)

PATTERN_URL = "https://rest.payamak-panel.com/api/SendSMS/BaseServiceNumber"
PLAIN_URL = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"


@register
class PayamakSmsProvider(NotificationProvider):
    """ملی‌پیامک: پترن اشتراکی (bodyId) برای OTP و ارسال متن آزاد برای بقیه."""

    codename = "payamak"
    label = "ملی‌پیامک (Payamak)"
    channel_type = ChannelType.SMS

    def validate_config(self, config: dict) -> None:
        if not config.get("username"):
            raise ValueError("username is required")
        if not config.get("password"):
            raise ValueError("password is required")

    def send(
        self,
        recipient: str,
        body: str,
        config: dict,
        subject: str = "",
        metadata: dict | None = None,
    ) -> SendResult:
        metadata = metadata or {}
        to = UserManager.normalize_phone(recipient)
        body_id = str(config.get("body_id") or "").strip()
        if metadata.get("purpose") == "otp" and body_id:
            text = str(metadata.get("otp_code") or body).strip()
            return self._post(
                PATTERN_URL,
                {
                    "username": config.get("username", ""),
                    "password": config.get("password", ""),
                    "text": text,
                    "to": to,
                    "bodyId": body_id,
                },
            )
        payload = {
            "username": config.get("username", ""),
            "password": config.get("password", ""),
            "to": to,
            "text": body,
        }
        from_number = str(config.get("from_number") or "").strip()
        if from_number:
            payload["from"] = from_number
        return self._post(PLAIN_URL, payload)

    def _post(self, url: str, fields: dict[str, str]) -> SendResult:
        data = urllib.parse.urlencode(fields).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                raw_body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            return SendResult(success=False, message=f"HTTP {exc.code}: {detail[:300]}")
        except urllib.error.URLError as exc:
            return SendResult(success=False, message=str(exc.reason or exc))

        try:
            payload = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            return SendResult(success=False, message=raw_body[:300] or "پاسخ نامعتبر از ملی‌پیامک")

        status = payload.get("RetStatus")
        value = str(payload.get("Value") or "")
        label = str(payload.get("StrRetStatus") or "")
        if status == 1:
            return SendResult(success=True, message=label or "Ok", external_id=value, raw=payload)
        return SendResult(
            success=False,
            message=label or value or f"RetStatus={status}",
            external_id=value,
            raw=payload,
        )
