"""Payment gateway base classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from payments.models import PaymentTransaction


@dataclass
class PaymentCreateResult:
    payment_url: str
    authority: str


@dataclass
class PaymentVerifyResult:
    success: bool
    ref_id: str = ""
    message: str = ""
    raw: dict | None = None


@dataclass
class PaymentRefundResult:
    success: bool
    refunded_amount: Decimal = Decimal("0")
    message: str = ""


class PaymentGateway(ABC):
    codename: str = ""
    label: str = ""

    @abstractmethod
    def create_payment(self, transaction: PaymentTransaction, config: dict, callback_url: str) -> PaymentCreateResult:
        pass

    @abstractmethod
    def verify_payment(self, transaction: PaymentTransaction, config: dict, params: dict) -> PaymentVerifyResult:
        pass

    def refund_payment(self, transaction: PaymentTransaction, config: dict, amount: Decimal) -> PaymentRefundResult:
        return PaymentRefundResult(success=False, message="Refund not supported")

    def parse_webhook(self, payload: dict) -> dict:
        return payload
