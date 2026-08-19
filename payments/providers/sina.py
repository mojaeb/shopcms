"""Sina Bank payment gateway."""

from payments.providers.base import PaymentVerifyResult
from payments.providers.registry import register
from payments.providers.sandbox import SandboxGateway


@register
class SinaGateway(SandboxGateway):
    """درگاه سینا — سندباکس فعال؛ پیاده‌سازی زنده هنوز تکمیل نشده."""

    codename = "sina"
    label = "سینا"

    def _create_live_payment(self, transaction, config, callback_url, authority):
        # TODO: پیاده‌سازی واقعی نیازمند مستندات رسمی درگاه بانک سینا است:
        #   1) endpoint درخواست پرداخت / توکن و پارامترهای پذیرنده (مثلاً terminal_id)
        #   2) فرمت callback و تطبیق authority در دیتابیس (store + gateway + authority)
        #   3) endpoint تأیید — مبلغ را فقط از transaction.amount بخوانید
        #   4) واحد پول و جدول کدهای خطا
        # نیاز به تایید مستندات رسمی بانک سینا — endpoint و پروتکل را حدس نزن.
        raise ValueError("درگاه سینا هنوز به‌صورت کامل پیاده‌سازی نشده است. با پشتیبانی تماس بگیرید.")

    def _verify_live(self, transaction, config, params):
        # TODO: تأیید زنده طبق مستندات رسمی بانک سینا — حدس نزن.
        return PaymentVerifyResult(
            success=False,
            message="درگاه سینا هنوز به‌صورت کامل پیاده‌سازی نشده است. با پشتیبانی تماس بگیرید.",
            raw=params,
        )
