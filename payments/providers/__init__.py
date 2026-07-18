"""Payment gateway implementations (sandbox-ready)."""

import secrets
from decimal import Decimal
from urllib.parse import urlencode

from payments.providers.base import (
    PaymentCreateResult,
    PaymentGateway,
    PaymentRefundResult,
    PaymentVerifyResult,
)
from payments.providers.registry import register


class SandboxGateway(PaymentGateway):
    """Base sandbox gateway with simulated redirect flow."""

    def _sandbox(self, config: dict) -> bool:
        return config.get("sandbox", True)

    def _build_sandbox_url(self, callback_url: str, authority: str, success: bool = True) -> str:
        params = urlencode({"Authority": authority, "Status": "OK" if success else "NOK"})
        separator = "&" if "?" in callback_url else "?"
        return f"{callback_url}{separator}{params}"

    def create_payment(self, transaction, config: dict, callback_url: str) -> PaymentCreateResult:
        authority = secrets.token_hex(16)
        if self._sandbox(config):
            payment_url = self._build_sandbox_url(callback_url, authority)
        else:
            payment_url = self._create_live_payment(transaction, config, callback_url, authority)
        return PaymentCreateResult(payment_url=payment_url, authority=authority)

    def _create_live_payment(self, transaction, config: dict, callback_url: str, authority: str) -> str:
        raise NotImplementedError("Live gateway not configured")

    def verify_payment(self, transaction, config: dict, params: dict) -> PaymentVerifyResult:
        status = params.get("Status", params.get("status", ""))
        if str(status).upper() not in ("OK", "SUCCESS", "100", "1"):
            return PaymentVerifyResult(success=False, message="پرداخت ناموفق بود")

        if self._sandbox(config):
            ref_id = params.get("RefID") or secrets.token_hex(6).upper()
            return PaymentVerifyResult(success=True, ref_id=str(ref_id), raw=params)

        return self._verify_live(transaction, config, params)

    def _verify_live(self, transaction, config: dict, params: dict) -> PaymentVerifyResult:
        raise NotImplementedError("Live verify not configured")

    def refund_payment(self, transaction, config: dict, amount: Decimal) -> PaymentRefundResult:
        if self._sandbox(config):
            return PaymentRefundResult(success=True, refunded_amount=amount, message="Sandbox refund OK")
        return PaymentRefundResult(success=False, message="Live refund not configured")


@register
class ZarinpalGateway(SandboxGateway):
    codename = "zarinpal"
    label = "زرین‌پال"


@register
class IDPayGateway(SandboxGateway):
    codename = "idpay"
    label = "آیدی‌پی"

    def verify_payment(self, transaction, config: dict, params: dict) -> PaymentVerifyResult:
        params = {**params, "Status": params.get("status", params.get("Status", "OK"))}
        return super().verify_payment(transaction, config, params)


@register
class MellatGateway(SandboxGateway):
    codename = "mellat"
    label = "ملت"


@register
class PasargadGateway(SandboxGateway):
    codename = "pasargad"
    label = "پاسارگاد"
