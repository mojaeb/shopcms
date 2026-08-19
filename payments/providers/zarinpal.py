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
    PaymentInquiryResult,
    PaymentRefundResult,
    PaymentVerifyResult,
)
from payments.providers.registry import register

logger = logging.getLogger(__name__)

_API_LIVE = "https://api.zarinpal.com/pg/v4/payment"
_API_SANDBOX = "https://sandbox.zarinpal.com/pg/v4/payment"
_START_LIVE = "https://www.zarinpal.com/pg/StartPay/{authority}"
_START_SANDBOX = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"
_GRAPHQL_URL = "https://next.zarinpal.com/api/v4/graphql"

_PLACEHOLDER_MERCHANTS = {
    "",
    "test",
    "sandbox",
    "sandbox-merchant",
}

_PAID_INQUIRY_STATUSES = {"PAID", "VERIFIED"}

# TODO: تطبیق نهایی با https://www.zarinpal.com/docs/paymentGateway/errorList.html
ZARINPAL_ERROR_CODES: dict[int, str] = {
    -9: "خطای اعتبارسنجی: مرچنت‌کد، آدرس بازگشت، توضیحات یا مبلغ نامعتبر است",
    -10: "آی‌پی یا مرچنت‌کد پذیرنده صحیح نیست",
    -11: "مرچنت‌کد فعال نیست. با پشتیبانی زرین‌پال تماس بگیرید",
    -12: "تلاش بیش از حد مجاز. کمی بعد دوباره تلاش کنید",
    -13: "محدودیت تراکنش. مدارک پذیرنده را در پنل زرین‌پال تکمیل کنید",
    -14: "آدرس بازگشت با دامنه ثبت‌شده درگاه مطابقت ندارد",
    -15: "درگاه پرداخت تعلیق شده است. با پشتیبانی زرین‌پال تماس بگیرید",
    -16: "سطح تأیید پذیرنده کافی نیست",
    -17: "محدودیت پذیرنده در سطح فعلی",
    -18: "امکان استفاده از این درگاه روی این دامنه وجود ندارد",
    -19: "امکان ایجاد تراکنش برای این ترمینال وجود ندارد",
    -30: "پذیرنده به سرویس تسویه اشتراکی دسترسی ندارد",
    -31: "حساب بانکی تسویه را در پنل اضافه کنید یا مقادیر تسهیم را بررسی کنید",
    -32: "مبلغ تسهیم از مبلغ کل تراکنش بیشتر است",
    -33: "درصدهای تسهیم صحیح نیست",
    -34: "مبلغ تسهیم از مبلغ کل تراکنش بیشتر است",
    -35: "تعداد افراد دریافت‌کننده تسهیم بیش از حد مجاز است",
    -36: "حداقل مبلغ تسهیم ۱۰٬۰۰۰ ریال است",
    -37: "یک یا چند شماره شبا برای تسهیم از سمت بانک غیرفعال است",
    -38: "شبا به‌درستی تعریف نشده است. کمی بعد دوباره تلاش کنید",
    -39: "خطای تسهیم. با پشتیبانی زرین‌پال تماس بگیرید",
    -40: "پارامترهای اضافی نامعتبر است",
    -41: "حداکثر مبلغ پرداختی ۱۰۰ میلیون تومان است",
    -50: "مبلغ پرداخت‌شده با مبلغ ارسال‌شده برای تأیید متفاوت است",
    -51: "پرداخت ناموفق",
    -52: "خطای غیرمنتظره. با پشتیبانی زرین‌پال تماس بگیرید",
    -53: "این پرداخت متعلق به این مرچنت‌کد نیست",
    -54: "اتوریتی نامعتبر است",
    -55: "تراکنش مورد نظر یافت نشد",
    -60: "امکان بازگشت این تراکنش با بانک وجود ندارد",
    -61: "تراکنش موفق نیست یا قبلاً بازگشت شده است",
    -62: "آی‌پی درگاه تنظیم نشده است",
    -63: "مهلت بازگشت این تراکنش به پایان رسیده است",
}

_SESSION_BY_AUTHORITY_QUERY = """
query SessionByAuthority($authority: String!) {
  Session(authority: $authority) {
    id
  }
}
""".strip()
# TODO: مستندات عمومی Session این فیلترها را فهرست کرده: terminal_id / id / reference_id / rrn
# (https://www.zarinpal.com/docs/apiDocs/query/session) — پارامتر authority نیاز به تایید مستندات رسمی دارد.

_ADD_REFUND_MUTATION = """
mutation AddRefund(
  $session_id: ID!
  $amount: BigInteger!
  $description: String
  $method: InstantPayoutActionTypeEnum
  $reason: RefundReasonEnum
) {
  resource: AddRefund(
    session_id: $session_id
    amount: $amount
    description: $description
    method: $method
    reason: $reason
  ) {
    terminal_id
    id
    amount
    timeline {
      refund_amount
      refund_time
      refund_status
    }
  }
}
""".strip()


@register
class ZarinpalGateway(PaymentGateway):
    """زرین‌پال — روش پرداخت اینترنتی (شبیه‌ساز / سندباکس / زنده)."""

    codename = "zarinpal"
    label = "زرین‌پال"

    def is_live_ready(self, config: dict | None = None) -> bool:
        return True

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

        data = self._post(self._api_base(config) + "/request.json", payload)
        code = self._response_code(data)
        if code != 100:
            message = self._error_message(data) or f"خطای زرین‌پال در ایجاد پرداخت (کد {code})"
            raise ValueError(message)

        authority = str((data.get("data") or {}).get("authority") or "")
        if not authority:
            raise ValueError("پاسخ زرین‌پال فاقد authority است")

        return PaymentCreateResult(
            payment_url=self._start_pay_url(config, authority),
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

        payload = {
            "merchant_id": merchant_id,
            "amount": self._amount_int(transaction.amount),
            "authority": authority,
        }
        try:
            data = self._post(self._api_base(config) + "/verify.json", payload)
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

    def inquiry_payment(self, transaction, config: dict) -> PaymentInquiryResult:
        authority = str(transaction.authority or "").strip()
        if not authority:
            return PaymentInquiryResult(success=False, message="کد authority یافت نشد")

        if self._should_simulate(config):
            return PaymentInquiryResult(
                success=True,
                status="PAID",
                message="Simulated inquiry OK",
                raw={"status": "PAID", "code": 100},
            )

        merchant_id = (config.get("merchant_id") or "").strip()
        if not merchant_id:
            return PaymentInquiryResult(success=False, message="کد پذیرنده زرین‌پال تنظیم نشده است")

        payload = {"merchant_id": merchant_id, "authority": authority}
        try:
            data = self._post(self._api_base(config) + "/inquiry.json", payload)
        except ValueError as exc:
            return PaymentInquiryResult(success=False, message=str(exc), raw={"error": str(exc)})

        body = data.get("data") if isinstance(data.get("data"), dict) else {}
        status = str((body or {}).get("status") or "").upper()
        code = self._response_code(data)
        if status in _PAID_INQUIRY_STATUSES and code in (100, 101):
            return PaymentInquiryResult(
                success=True,
                status=status,
                message=str((body or {}).get("message") or "Success"),
                raw=data,
            )

        message = self._error_message(data)
        if not message:
            if status:
                message = f"وضعیت استعلام: {status}"
            else:
                message = f"استعلام پرداخت ناموفق (کد {code})"
        return PaymentInquiryResult(success=False, status=status, message=message, raw=data)

    def refund_payment(self, transaction, config: dict, amount: Decimal) -> PaymentRefundResult:
        if self._should_simulate(config):
            return PaymentRefundResult(success=True, refunded_amount=amount, message="Sandbox refund OK")

        access_token = (config.get("access_token") or "").strip()
        if not access_token:
            return PaymentRefundResult(
                success=False,
                message="بازگشت وجه زرین‌پال از طریق پنل پذیرنده انجام می‌شود",
            )

        authority = str(transaction.authority or "").strip()
        if not authority:
            return PaymentRefundResult(success=False, message="کد authority برای بازگشت وجه یافت نشد")

        try:
            session_data = self._graphql_post(
                _SESSION_BY_AUTHORITY_QUERY,
                {"authority": authority},
                access_token,
                url=self._graphql_endpoint(config),
            )
        except ValueError as exc:
            return PaymentRefundResult(success=False, message=str(exc))

        session_id = self._session_id(session_data)
        if not session_id:
            message = self._graphql_error_message(session_data) or "شناسه نشست زرین‌پال یافت نشد"
            return PaymentRefundResult(success=False, message=message)

        description = f"بازگشت وجه {transaction.tracking_code}"
        try:
            refund_data = self._graphql_post(
                _ADD_REFUND_MUTATION,
                {
                    "session_id": session_id,
                    "amount": self._amount_int(amount),
                    "description": description,
                    "method": "PAYA",
                    "reason": "CUSTOMER_REQUEST",
                },
                access_token,
                url=self._graphql_endpoint(config),
            )
        except ValueError as exc:
            return PaymentRefundResult(success=False, message=str(exc))

        resource = (refund_data.get("data") or {}).get("resource") or {}
        timeline = resource.get("timeline") if isinstance(resource, dict) else {}
        status = str((timeline or {}).get("refund_status") or "").upper()
        if status in ("PENDING", "SUCCESS"):
            return PaymentRefundResult(
                success=True,
                refunded_amount=amount,
                message="درخواست بازگشت وجه ثبت شد",
            )

        message = self._graphql_error_message(refund_data) or "بازگشت وجه زرین‌پال ناموفق بود"
        return PaymentRefundResult(success=False, message=message)

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
    def _normalize_url(url: str) -> str:
        return (url or "").strip().rstrip("/")

    @classmethod
    def _api_base(cls, config: dict) -> str:
        override = cls._normalize_url(str(config.get("api_base") or config.get("api_url") or ""))
        if override:
            return override
        return _API_SANDBOX if bool(config.get("sandbox", True)) else _API_LIVE

    @classmethod
    def _start_pay_url(cls, config: dict, authority: str) -> str:
        tpl = (config.get("start_pay_url") or "").strip()
        if not tpl:
            tpl = _START_SANDBOX if bool(config.get("sandbox", True)) else _START_LIVE
        if "{authority}" not in tpl:
            tpl = tpl.rstrip("/") + "/{authority}"
        return tpl.format(authority=authority)

    @classmethod
    def _graphql_endpoint(cls, config: dict) -> str:
        override = cls._normalize_url(str(config.get("graphql_url") or ""))
        return override or _GRAPHQL_URL

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
        extracted = ZarinpalGateway._extract_error_code(data)
        return extracted if extracted is not None else -1

    @staticmethod
    def _extract_error_code(data: dict) -> int | None:
        errors = data.get("errors")
        if isinstance(errors, dict):
            if "code" in errors:
                try:
                    return int(errors["code"])
                except (TypeError, ValueError):
                    pass
            for value in errors.values():
                if not isinstance(value, list):
                    continue
                for item in reversed(value):
                    try:
                        return int(item)
                    except (TypeError, ValueError):
                        continue
        if isinstance(errors, list):
            for item in errors:
                if isinstance(item, dict) and "code" in item:
                    try:
                        return int(item["code"])
                    except (TypeError, ValueError):
                        continue
        return None

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
                msg = first.get("message")
                if msg:
                    return str(msg)
            elif first:
                return str(first)
        body = data.get("data")
        if isinstance(body, dict) and body.get("message"):
            return str(body["message"])

        code = ZarinpalGateway._extract_error_code(data)
        if code in ZARINPAL_ERROR_CODES:
            return ZARINPAL_ERROR_CODES[code]
        return ""

    @staticmethod
    def _session_id(data: dict) -> str:
        session = (data.get("data") or {}).get("Session")
        if isinstance(session, list) and session:
            session = session[0]
        if isinstance(session, dict):
            return str(session.get("id") or "")
        return ""

    @staticmethod
    def _graphql_error_message(data: dict) -> str:
        errors = data.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict) and first.get("message"):
                return str(first["message"])
            return str(first)
        return ""

    @staticmethod
    def _authorization_header(access_token: str) -> str:
        token = access_token.strip()
        if token.lower().startswith("bearer "):
            return token
        return f"Bearer {token}"

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

    def _graphql_post(self, query: str, variables: dict, access_token: str, url: str | None = None) -> dict:
        payload = {"query": query, "variables": variables}
        body = json.dumps(payload).encode("utf-8")
        endpoint = self._normalize_url(url or "") or _GRAPHQL_URL
        req = urllib.request.Request(
            endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": self._authorization_header(access_token),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            logger.warning("Zarinpal GraphQL HTTP %s: %s", exc.code, raw[:500])
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError as decode_exc:
                raise ValueError(f"خطای ارتباط با زرین‌پال (HTTP {exc.code})") from decode_exc
            message = self._graphql_error_message(data) or f"خطای ارتباط با زرین‌پال (HTTP {exc.code})"
            raise ValueError(message) from exc
        except urllib.error.URLError as exc:
            logger.warning("Zarinpal GraphQL connection error: %s", exc)
            raise ValueError("ارتباط با زرین‌پال برقرار نشد") from exc

        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            raise ValueError("پاسخ نامعتبر از زرین‌پال") from exc
