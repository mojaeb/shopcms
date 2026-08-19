"""Payment gateway implementations."""

from payments.providers.base import PaymentVerifyResult
from payments.providers.registry import register
from payments.providers.sandbox import SandboxGateway

# Register first-class gateways (import side-effect).
from payments.providers.zarinpal import ZarinpalGateway  # noqa: F401
from payments.providers.mellat import MellatGateway  # noqa: F401
from payments.providers.pasargad import PasargadGateway  # noqa: F401
from payments.providers.sina import SinaGateway  # noqa: F401

__all__ = [
    "SandboxGateway",
    "IDPayGateway",
    "ZarinpalGateway",
    "MellatGateway",
    "PasargadGateway",
    "SinaGateway",
]


@register
class IDPayGateway(SandboxGateway):
    codename = "idpay"
    label = "آیدی‌پی"

    def verify_payment(self, transaction, config: dict, params: dict) -> PaymentVerifyResult:
        params = {**params, "Status": params.get("status", params.get("Status", "OK"))}
        return super().verify_payment(transaction, config, params)
