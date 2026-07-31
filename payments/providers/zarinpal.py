"""Zarinpal payment gateway (simulate / sandbox API / live REST v4)."""

from __future__ import annotations

import json
import logging
import secrets
import urllib.error
import urllib.request
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode

from payments.providers.base import (
    PaymentCreateResult,
    PaymentGateway,
    PaymentRefundResult,
    PaymentVerifyResult,
)
from payments.providers.registry import register

logger = logging.getLogger(__name__)

_API_LIVE = "https://api.zarinpal.com/pg/v4/payment"
_API_SANDBOX = "https://sandbox.zarinpal.com/pg/v4/payment"
_START_LIVE = "https://www.zarinpal.com/pg/StartPay/{authority}"
_START_SANDBOX = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"

_PLACEHOLDER_MERCHANTS = {
    "",
    "test",
    "sandbox",
    "sandbox-merchant",
}


@register
class ZarinpalGateway(PaymentGateway):
    """زرین‌پال — روش پرداخت اینترنتی (شبیه‌ساز / سندباکس / زنده)."""

    codename = "zarinpal"
    label = "زرین‌پال"

    def create_payment(self, transaction, config: dict, callback_url: str) -> PaymentCreateResult:
        merchant_id = (config.get("merchant_id") or "").strip()
        if not merchant_id:
            raise ValueError("کد پذیرنده زرین‌پال (merchant_id) تنظیم نشده است")

        if self._should_simulate(config):
            authority = f"S{secrets.token_hex(15)}"
            params = urlencode({"Authority": authority, "Status": "OK"})
            sep = "&" if "?" in callback_url else "?"
            return PaymentCreateResult(
                payment_url=f"{callback_url}{sep}{params}",
                authority=authority,
            )

        sandbox = bool(config.get("sandbox", True))
        amount = self._amount_int(transaction.amount)
        currency = self._currency(config, transaction)
        description = config.get("description") or f"پرداخت سفارش {transaction.tracking_code}"

        payload = {
            "merchant_id": merchant_id,
            "amount": amount,
            "callback_url": callback_url,
            "description": description,
            "currency": currency,
        }
        metadata = {}
        if config.get("mobile"):
            metadata["mobile"] = str(config["mobile"])
        if config.get("email"):
            metadata["email"] = str(config["email"])
        if metadata:
            payload["metadata"] = metadata

        data = self._post(self._api_base(sandbox) + "/request.json", payload)
        code = self._response_code(data)
        if code != 100:
            message = self._error_message(data) or f"خطای زرین‌پال در ایجاد پرداخت (کد {code})"
            raise ValueError(message)

        authority = str((data.get("data") or {}).get("authority") or "")
        if not authority:
            raise ValueError("پاسخ زرین‌پال فاقد authority است")

        start_tpl = _START_SANDBOX if sandbox else _START_LIVE
        return PaymentCreateResult(
            payment_url=start_tpl.format(authority=authority),
            authority=authority,
        )

    def verify_payment(self, transaction, config: dict, params: dict) -> PaymentVerifyResult:
        status = str(params.get("Status") or params.get("status") or "").upper()
        authority = str(
            params.get("Authority")
            or params.get("authority")
            or transaction.authority
            or ""
        )

        if status not in ("OK", "SUCCESS"):
            return PaymentVerifyResult(
                success=False,
                message="پرداخت توسط کاربر لغو یا ناموفق شد",
                raw=params,
            )
        if not authority:
            return PaymentVerifyResult(success=False, message="کد authority یافت نشد", raw=params)

        if self._should_simulate(config):
            ref_id = str(params.get("RefID") or secrets.token_hex(6).upper())
            return PaymentVerifyResult(success=True, ref_id=ref_id, message="Simulated OK", raw=params)

        merchant_id = (config.get("merchant_id") or "").strip()
        if not merchant_id:
            return PaymentVerifyResult(success=False, message="کد پذیرنده زرین‌پال تنظیم نشده است")

        sandbox = bool(config.get("sandbox", True))
        payload = {
            "merchant_id": merchant_id,
            "amount": self._amount_int(transaction.amount),
            "authority": authority,
        }
        try:
            data = self._post(self._api_base(sandbox) + "/verify.json", payload)
        except ValueError as exc:
            return PaymentVerifyResult(success=False, message=str(exc), raw={"error": str(exc)})

        code = self._response_code(data)
        body = data.get("data") or {}
        if code in (100, 101):
            ref_id = str(body.get("ref_id") or "")
            return PaymentVerifyResult(
                success=True,
                ref_id=ref_id,
                message="Verified" if code == 100 else "Already verified",
                raw=data,
            )

        message = self._error_message(data) or f"تأیید پرداخت ناموفق (کد {code})"
        return PaymentVerifyResult(success=False, message=message, raw=data)

    def refund_payment(self, transaction, config: dict, amount: Decimal) -> PaymentRefundResult:
        if self._should_simulate(config):
            return PaymentRefundResult(success=True, refunded_amount=amount, message="Sandbox refund OK")
        return PaymentRefundResult(
            success=False,
            message="بازگشت وجه زرین‌پال از طریق پنل پذیرنده انجام می‌شود",
        )

    def parse_webhook(self, payload: dict) -> dict:
        return {
            "Authority": payload.get("Authority") or payload.get("authority"),
            "Status": payload.get("Status") or payload.get("status"),
            **payload,
        }

    def _should_simulate(self, config: dict) -> bool:
        """Local simulate for tests/seed; real HTTP when simulate=false or real merchant UUID."""
        if "simulate" in config:
            return bool(config.get("simulate"))
        if not config.get("sandbox", True):
            return False
        mid = (config.get("merchant_id") or "").strip().lower()
        return mid in _PLACEHOLDER_MERCHANTS or mid.startswith("sandbox") or mid.startswith("test")

    @staticmethod
    def _api_base(sandbox: bool) -> str:
        return _API_SANDBOX if sandbox else _API_LIVE

    @staticmethod
    def _amount_int(amount) -> int:
        value = Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(value)

    @staticmethod
    def _currency(config: dict, transaction) -> str:
        raw = (
            config.get("currency")
            or getattr(getattr(transaction, "store", None), "currency", None)
            or "IRR"
        )
        raw = str(raw).upper()
        if raw in ("IRT", "TOMAN", "TMN"):
            return "IRT"
        return "IRR"

    @staticmethod
    def _response_code(data: dict) -> int:
        body = data.get("data")
        if isinstance(body, dict) and "code" in body:
            try:
                return int(body["code"])
            except (TypeError, ValueError):
                return -1
        errors = data.get("errors")
        if isinstance(errors, dict) and "code" in errors:
            try:
                return int(errors["code"])
            except (TypeError, ValueError):
                return -1
        return -1

    @staticmethod
    def _error_message(data: dict) -> str:
        errors = data.get("errors")
        if isinstance(errors, dict):
            msg = errors.get("message")
            if msg:
                return str(msg)
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                return str(first.get("message") or first)
            return str(first)
        body = data.get("data")
        if isinstance(body, dict) and body.get("message"):
            return str(body["message"])
        return ""

    def _post(self, url: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            logger.warning("Zarinpal HTTP %s: %s", exc.code, raw[:500])
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError as decode_exc:
                raise ValueError(f"خطای ارتباط با زرین‌پال (HTTP {exc.code})") from decode_exc
            message = self._error_message(data) or f"خطای ارتباط با زرین‌پال (HTTP {exc.code})"
            raise ValueError(message) from exc
        except urllib.error.URLError as exc:
            logger.warning("Zarinpal connection error: %s", exc)
            raise ValueError("ارتباط با زرین‌پال برقرار نشد") from exc

        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise ValueError("پاسخ نامعتبر از زرین‌پال") from exc
