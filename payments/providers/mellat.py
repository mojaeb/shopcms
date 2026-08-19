"""Mellat (Behpardakht) payment gateway."""

from payments.providers.base import PaymentVerifyResult
from payments.providers.registry import register
from payments.providers.sandbox import SandboxGateway


@register
class MellatGateway(SandboxGateway):
    """درگاه ملت — سندباکس فعال؛ پیاده‌سازی زنده هنوز تکمیل نشده."""

    codename = "mellat"
    label = "ملت"

    def _create_live_payment(self, transaction, config, callback_url, authority):
        # TODO: پیاده‌سازی واقعی نیازمند مستندات رسمی درگاه ملت (IPG) است:
        #   1) endpoint درخواست توکن (معمولاً SOAP یا REST bpPayRequest با terminalId/userName/userPassword)
        #   2) فرمت callback (RefId/ResCode/SaleOrderId/SaleReferenceId)
        #   3) endpoint تسویه (bpVerifyRequest + bpSettleRequest، دو مرحله‌ای برخلاف زرین‌پال)
        #   4) واحد پول: ریال — مبلغ را فقط از transaction.amount بخوانید، نه از ورودی کاربر
        #   5) جدول کدهای خطا (ResCode)
        # نیاز به تایید مستندات رسمی Behpardakht / بانک ملت.
        raise ValueError("درگاه ملت هنوز به‌صورت کامل پیاده‌سازی نشده است. با پشتیبانی تماس بگیرید.")

    def _verify_live(self, transaction, config, params):
        # TODO: همان مستندات رسمی bpVerifyRequest + bpSettleRequest — حدس نزن.
        return PaymentVerifyResult(
            success=False,
            message="درگاه ملت هنوز به‌صورت کامل پیاده‌سازی نشده است. با پشتیبانی تماس بگیرید.",
            raw=params,
        )
