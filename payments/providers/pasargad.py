"""Pasargad payment gateway."""

from payments.providers.base import PaymentVerifyResult
from payments.providers.registry import register
from payments.providers.sandbox import SandboxGateway


@register
class PasargadGateway(SandboxGateway):
    """درگاه پاسارگاد — سندباکس فعال؛ پیاده‌سازی زنده هنوز تکمیل نشده."""

    codename = "pasargad"
    label = "پاسارگاد"

    def _create_live_payment(self, transaction, config, callback_url, authority):
        # TODO: پیاده‌سازی واقعی نیازمند مستندات رسمی درگاه پاسارگاد (PEP / IPG) است:
        #   1) احراز هویت با گواهی RSA / certificate — نه فقط merchant_code ساده
        #      (terminal_id و merchant_code در seed فعلی صرفاً placeholder هستند)
        #   2) endpoint دریافت توکن پرداخت و آدرس redirect
        #   3) فرمت callback و پارامترهای تأیید
        #   4) واحد پول: ریال — مبلغ را فقط از transaction.amount بخوانید
        #   5) جدول کدهای خطا
        # نیاز به تایید مستندات رسمی بانک پاسارگاد.
        raise ValueError("درگاه پاسارگاد هنوز به‌صورت کامل پیاده‌سازی نشده است. با پشتیبانی تماس بگیرید.")

    def _verify_live(self, transaction, config, params):
        # TODO: تأیید زنده با امضای RSA طبق مستندات رسمی — حدس نزن.
        return PaymentVerifyResult(
            success=False,
            message="درگاه پاسارگاد هنوز به‌صورت کامل پیاده‌سازی نشده است. با پشتیبانی تماس بگیرید.",
            raw=params,
        )
