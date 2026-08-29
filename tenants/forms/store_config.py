"""Admin form for unified store configuration."""

from __future__ import annotations

import json
import re

from django import forms

from accounts.managers import UserManager
from payments.enums import GatewayType
from shipping.enums import ShippingProviderType
from tenants.models import Store
from tenants.services.store_config import StoreConfigService
from unfold.widgets import (
    UnfoldAdminCheckboxSelectMultipleWidget,
    UnfoldAdminColorInputWidget,
    UnfoldAdminEmailInputWidget,
    UnfoldAdminSelectWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminTextInputWidget,
    UnfoldAdminURLInputWidget,
    UnfoldBooleanSwitchWidget,
)


class StoreConfigForm(forms.ModelForm):
    """Store model fields plus structured settings from StoreSetting / LayoutSettings."""

    theme_logo = forms.CharField(
        required=False,
        label="لوگو (URL)",
        widget=UnfoldAdminURLInputWidget(attrs={"placeholder": "https://..."}),
    )
    theme_color_primary = forms.CharField(
        required=False,
        label="رنگ اصلی",
        widget=UnfoldAdminColorInputWidget(),
    )
    theme_color_background = forms.CharField(
        required=False,
        label="رنگ پس‌زمینه",
        widget=UnfoldAdminColorInputWidget(),
    )
    theme_color_text = forms.CharField(
        required=False,
        label="رنگ متن",
        widget=UnfoldAdminColorInputWidget(),
    )
    trust_enamad_image = forms.CharField(
        required=False,
        label="اینماد — تصویر",
        widget=UnfoldAdminURLInputWidget(attrs={"placeholder": "https://..."}),
    )
    trust_enamad_link = forms.CharField(
        required=False,
        label="اینماد — لینک",
        widget=UnfoldAdminURLInputWidget(attrs={"placeholder": "https://trustseal.enamad.ir/..."}),
    )
    trust_badge2_image = forms.CharField(
        required=False,
        label="نشان دوم — تصویر",
        widget=UnfoldAdminURLInputWidget(attrs={"placeholder": "https://..."}),
    )
    trust_badge2_link = forms.CharField(
        required=False,
        label="نشان دوم — لینک",
        widget=UnfoldAdminURLInputWidget(attrs={"placeholder": "https://..."}),
    )

    contact_phone = forms.CharField(
        required=False,
        label="تلفن",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "۰۲۱-..."}),
    )
    contact_email = forms.EmailField(
        required=False,
        label="ایمیل",
        widget=UnfoldAdminEmailInputWidget(attrs={"placeholder": "info@example.com", "dir": "ltr"}),
    )
    contact_address = forms.CharField(
        required=False,
        label="آدرس",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}),
    )
    contact_whatsapp = forms.CharField(
        required=False,
        label="واتساپ",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "0912...", "dir": "ltr"}),
    )
    social_instagram = forms.CharField(
        required=False,
        label="اینستاگرام",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "https://instagram.com/...", "dir": "ltr"}),
    )
    social_telegram = forms.CharField(
        required=False,
        label="تلگرام",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "https://t.me/...", "dir": "ltr"}),
    )
    social_twitter = forms.CharField(
        required=False,
        label="توییتر / X",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "https://x.com/...", "dir": "ltr"}),
    )
    social_linkedin = forms.CharField(
        required=False,
        label="لینکدین",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "https://linkedin.com/...", "dir": "ltr"}),
    )
    social_youtube = forms.CharField(
        required=False,
        label="یوتیوب",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "https://youtube.com/...", "dir": "ltr"}),
    )

    seo_meta_title = forms.CharField(
        required=False,
        label="عنوان SEO",
        max_length=200,
        widget=UnfoldAdminTextInputWidget(),
    )
    seo_meta_description = forms.CharField(
        required=False,
        label="توضیح SEO",
        max_length=500,
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2}),
    )
    seo_meta_keywords = forms.CharField(
        required=False,
        label="کلمات کلیدی",
        max_length=500,
        widget=UnfoldAdminTextInputWidget(),
    )
    seo_og_image = forms.CharField(
        required=False,
        label="تصویر Open Graph",
        widget=UnfoldAdminURLInputWidget(attrs={"placeholder": "https://..."}),
    )
    seo_robots = forms.CharField(
        required=False,
        label="Robots",
        initial="index,follow",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    seo_canonical_url = forms.CharField(
        required=False,
        label="URL کانونیکال",
        widget=UnfoldAdminURLInputWidget(attrs={"placeholder": "https://...", "dir": "ltr"}),
    )
    seo_google_site_verification = forms.CharField(
        required=False,
        label="تأیید گوگل سرچ کنسول",
        help_text="تگ HTML یا توکن google-site-verification، یا نام فایل googleXXXX.html",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 2, "dir": "ltr", "placeholder": 'content="…" یا google123.html'}),
    )

    tax_on_shipping = forms.BooleanField(
        required=False,
        label="مالیات روی ارسال",
        widget=UnfoldBooleanSwitchWidget,
    )

    payment_default_gateway = forms.ChoiceField(
        required=False,
        label="درگاه پیش‌فرض",
        choices=[("", "— انتخاب کنید —"), *GatewayType.choices],
        widget=UnfoldAdminSelectWidget,
    )
    payment_gateways = forms.MultipleChoiceField(
        required=False,
        label="درگاه‌های فعال",
        choices=GatewayType.choices,
        widget=UnfoldAdminCheckboxSelectMultipleWidget,
    )
    zarinpal_merchant_id = forms.CharField(
        required=False,
        label="زرین‌پال — Merchant ID",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    zarinpal_sandbox = forms.BooleanField(
        required=False,
        label="زرین‌پال — حالت آزمایشی",
        widget=UnfoldBooleanSwitchWidget,
    )
    payment_callback_base_url = forms.URLField(
        required=False,
        assume_scheme="https",
        label="آدرس پایه بازگشت پرداخت (Callback)",
        help_text="مثلاً https://shop.example.com — اگر خالی باشد از دامنهٔ فعلی درخواست استفاده می‌شود.",
        widget=UnfoldAdminURLInputWidget(attrs={"dir": "ltr", "placeholder": "https://..."}),
    )
    zarinpal_api_base = forms.CharField(
        required=False,
        label="زرین‌پال — آدرس API",
        help_text="خالی = پیش‌فرض رسمی. مثال زنده: https://api.zarinpal.com/pg/v4/payment",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr", "placeholder": "https://api.zarinpal.com/pg/v4/payment"}),
    )
    zarinpal_start_pay_url = forms.CharField(
        required=False,
        label="زرین‌پال — آدرس شروع پرداخت",
        help_text="باید شامل {authority} باشد. مثال: https://www.zarinpal.com/pg/StartPay/{authority}",
        widget=UnfoldAdminTextInputWidget(
            attrs={"dir": "ltr", "placeholder": "https://www.zarinpal.com/pg/StartPay/{authority}"}
        ),
    )
    zarinpal_graphql_url = forms.CharField(
        required=False,
        label="زرین‌پال — آدرس GraphQL (ریفاند)",
        help_text="خالی = https://next.zarinpal.com/api/v4/graphql",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr", "placeholder": "https://next.zarinpal.com/api/v4/graphql"}),
    )

    shipping_origin_city = forms.CharField(
        required=False,
        label="شهر مبدا",
        help_text="برای محاسبه تعرفه منطقه‌ای (هم‌استان / مجاور / دورافتاده) استفاده می‌شود.",
        widget=UnfoldAdminTextInputWidget(),
    )
    shipping_origin_province = forms.CharField(
        required=False,
        label="استان مبدا",
        help_text="نام فارسی استان (مثلاً خراسان رضوی، تهران).",
        widget=UnfoldAdminTextInputWidget(),
    )
    shipping_providers = forms.MultipleChoiceField(
        required=False,
        label="ارائه‌دهندگان فعال",
        choices=ShippingProviderType.choices,
        help_text="برای راهنمای پنل؛ روش‌های واقعی ارسال در بخش «ارسال» تعریف می‌شوند.",
        widget=UnfoldAdminCheckboxSelectMultipleWidget,
    )
    shipping_default_provider = forms.ChoiceField(
        required=False,
        label="ارائه‌دهنده پیش‌فرض",
        choices=[("", "— انتخاب کنید —"), *ShippingProviderType.choices],
        widget=UnfoldAdminSelectWidget,
    )
    shipping_free_threshold = forms.DecimalField(
        required=False,
        label="آستانه ارسال رایگان (فروشگاه)",
        min_value=0,
        decimal_places=0,
        max_digits=12,
        help_text="اگر جمع سبد به این مبلغ برسد، گزینه ارسال رایگان سطح فروشگاه نمایش داده می‌شود.",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr", "placeholder": "0"}),
    )
    shipping_base_package_weight_kg = forms.DecimalField(
        required=False,
        label="وزن بسته‌بندی (کیلوگرم)",
        min_value=0,
        decimal_places=3,
        max_digits=8,
        help_text="به مجموع وزن محصولات سبد اضافه می‌شود. خالی یا ۰ یعنی بدون وزن بسته‌بندی.",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr", "placeholder": "0.100"}),
    )

    # --- Advanced form tab (gateways + shipping snippets); optional JSON override per section ---
    idpay_api_key = forms.CharField(
        required=False,
        label="آیدی‌پی — API Key",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    idpay_sandbox = forms.BooleanField(
        required=False,
        label="آیدی‌پی — آزمایشی",
        widget=UnfoldBooleanSwitchWidget,
    )
    idpay_use_json = forms.BooleanField(
        required=False,
        label="آیدی‌پی — ذخیره از JSON",
        help_text="اگر JSON را عوض کنید همان ذخیره می‌شود. این سوییچ برای اجبار JSON است.",
        widget=UnfoldBooleanSwitchWidget,
    )
    idpay_json = forms.CharField(
        required=False,
        label="آیدی‌پی — JSON",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 6, "dir": "ltr", "spellcheck": "false"}),
    )

    mellat_terminal_id = forms.CharField(
        required=False,
        label="ملت — Terminal ID",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    mellat_username = forms.CharField(
        required=False,
        label="ملت — نام کاربری",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    mellat_password = forms.CharField(
        required=False,
        label="ملت — رمز",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    mellat_sandbox = forms.BooleanField(
        required=False,
        label="ملت — آزمایشی",
        widget=UnfoldBooleanSwitchWidget,
    )
    mellat_use_json = forms.BooleanField(
        required=False,
        label="ملت — ذخیره از JSON",
        widget=UnfoldBooleanSwitchWidget,
    )
    mellat_json = forms.CharField(
        required=False,
        label="ملت — JSON",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 6, "dir": "ltr", "spellcheck": "false"}),
    )

    pasargad_merchant_code = forms.CharField(
        required=False,
        label="پاسارگاد — Merchant Code",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    pasargad_terminal_id = forms.CharField(
        required=False,
        label="پاسارگاد — Terminal ID",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    pasargad_sandbox = forms.BooleanField(
        required=False,
        label="پاسارگاد — آزمایشی",
        widget=UnfoldBooleanSwitchWidget,
    )
    pasargad_use_json = forms.BooleanField(
        required=False,
        label="پاسارگاد — ذخیره از JSON",
        widget=UnfoldBooleanSwitchWidget,
    )
    pasargad_json = forms.CharField(
        required=False,
        label="پاسارگاد — JSON",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 6, "dir": "ltr", "spellcheck": "false"}),
    )

    sina_terminal_id = forms.CharField(
        required=False,
        label="سینا — Terminal ID",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    sina_sandbox = forms.BooleanField(
        required=False,
        label="سینا — آزمایشی",
        widget=UnfoldBooleanSwitchWidget,
    )
    sina_use_json = forms.BooleanField(
        required=False,
        label="سینا — ذخیره از JSON",
        widget=UnfoldBooleanSwitchWidget,
    )
    sina_json = forms.CharField(
        required=False,
        label="سینا — JSON",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 5, "dir": "ltr", "spellcheck": "false"}),
    )

    ship_post_fixed_price = forms.DecimalField(
        required=False,
        label="اسنیپت پست — قیمت ثابت",
        min_value=0,
        decimal_places=0,
        max_digits=12,
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    ship_post_max_weight_kg = forms.DecimalField(
        required=False,
        label="اسنیپت پست — سقف وزن (کیلو)",
        min_value=0,
        decimal_places=3,
        max_digits=8,
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    ship_post_use_json = forms.BooleanField(
        required=False,
        label="پست — ذخیره از JSON",
        widget=UnfoldBooleanSwitchWidget,
    )
    ship_post_json = forms.CharField(
        required=False,
        label="پست — JSON",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 5, "dir": "ltr", "spellcheck": "false"}),
    )

    ship_tipax_fixed_price = forms.DecimalField(
        required=False,
        label="اسنیپت تیپاکس — قیمت ثابت",
        min_value=0,
        decimal_places=0,
        max_digits=12,
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    ship_tipax_use_json = forms.BooleanField(
        required=False,
        label="تیپاکس — ذخیره از JSON",
        widget=UnfoldBooleanSwitchWidget,
    )
    ship_tipax_json = forms.CharField(
        required=False,
        label="تیپاکس — JSON",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 5, "dir": "ltr", "spellcheck": "false"}),
    )

    ship_peyk_fixed_price = forms.DecimalField(
        required=False,
        label="اسنیپت پیک — قیمت ثابت",
        min_value=0,
        decimal_places=0,
        max_digits=12,
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr"}),
    )
    ship_peyk_delivery_cities = forms.CharField(
        required=False,
        label="اسنیپت پیک — شهرهای مجاز",
        help_text="با ویرگول جدا کنید. خالی = همه شهرها.",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "مشهد, تهران"}),
    )
    ship_peyk_use_json = forms.BooleanField(
        required=False,
        label="پیک — ذخیره از JSON",
        widget=UnfoldBooleanSwitchWidget,
    )
    ship_peyk_json = forms.CharField(
        required=False,
        label="پیک — JSON",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 5, "dir": "ltr", "spellcheck": "false"}),
    )

    theme_hero_slides_json = forms.CharField(
        required=False,
        label="اسلایدر تم — JSON آرایه slides",
        help_text="آرایهٔ اسلایدها با ذخیره همین تب اعمال می‌شود.",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 10, "dir": "ltr", "spellcheck": "false"}),
    )
    theme_hero_use_json = forms.BooleanField(
        required=False,
        label="اسلایدر تم — ذخیره از JSON",
        help_text="دیگر لازم نیست؛ اسلایدهای این کادر با ذخیره اعمال می‌شوند.",
        widget=UnfoldBooleanSwitchWidget,
    )

    storage_driver = forms.CharField(
        required=False,
        label="درایور ذخیره‌سازی",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "local", "dir": "ltr"}),
    )

    sms_otp_provider = forms.ChoiceField(
        required=False,
        label="ارسال‌کننده OTP",
        choices=(
            ("console_sms", "فقط لاگ (محیط توسعه)"),
            ("payamak", "ملی‌پیامک / Payamak"),
        ),
        initial="console_sms",
        widget=UnfoldAdminSelectWidget,
    )
    sms_payamak_username = forms.CharField(
        required=False,
        label="ملی‌پیامک — نام کاربری",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr", "autocomplete": "off"}),
    )
    sms_payamak_password = forms.CharField(
        required=False,
        label="ملی‌پیامک — رمز عبور",
        help_text="خالی بگذارید تا رمز قبلی حفظ شود.",
        widget=UnfoldAdminTextInputWidget(
            attrs={"dir": "ltr", "autocomplete": "new-password", "type": "password"}
        ),
    )
    sms_payamak_body_id = forms.CharField(
        required=False,
        label="ملی‌پیامک — شناسه پترن (bodyId)",
        help_text="از پنل ملی‌پیامک → خدمات اشتراکی. برای OTP فقط خود کد به‌عنوان text ارسال می‌شود.",
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr", "placeholder": "226930"}),
    )
    sms_otp_template = forms.CharField(
        required=False,
        label="متن پیامک OTP",
        help_text="برای ارسال متن آزاد از {code} استفاده کنید. اگر پترن bodyId ست باشد این متن برای OTP استفاده نمی‌شود.",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 3}),
    )

    layout_use_custom_header = forms.BooleanField(
        required=False,
        label="هدر سفارشی",
        widget=UnfoldBooleanSwitchWidget,
    )
    layout_use_custom_footer = forms.BooleanField(
        required=False,
        label="فوتر سفارشی",
        widget=UnfoldBooleanSwitchWidget,
    )
    layout_header_html = forms.CharField(
        required=False,
        label="HTML هدر",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 4, "dir": "ltr"}),
    )
    layout_footer_html = forms.CharField(
        required=False,
        label="HTML فوتر",
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 4, "dir": "ltr"}),
    )

    store_manager_phone = forms.CharField(
        required=False,
        label="موبایل مدیر",
        help_text="با ذخیره، این شخص مدیر اصلی فروشگاه می‌شود. برای عوض کردن، شماره جدید را وارد کنید.",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "0912...", "dir": "ltr"}),
    )
    store_manager_first_name = forms.CharField(
        required=False,
        label="نام مدیر",
        widget=UnfoldAdminTextInputWidget(),
    )
    store_manager_last_name = forms.CharField(
        required=False,
        label="نام خانوادگی مدیر",
        widget=UnfoldAdminTextInputWidget(),
    )

    class Meta:
        model = Store
        fields = (
            "name",
            "slug",
            "store_type",
            "status",
            "theme",
            "default_theme",
            "currency",
            "timezone",
            "language",
            "tax_enabled",
            "tax_percent",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and not self.is_bound:
            for name, value in StoreConfigService().get_admin_initial(self.instance).items():
                if name in self.fields:
                    self.fields[name].initial = value
            from accounts.services.store_manager import StoreManagerService

            for name, value in StoreManagerService().admin_initial(self.instance).items():
                if name in self.fields:
                    self.fields[name].initial = value

    def save_related_config(self) -> None:
        """Persist structured settings after the Store instance is saved."""
        StoreConfigService().save_admin_data(self.instance, self.cleaned_data)
        if self.is_bound and "store_manager_phone" in self.data:
            from accounts.services.store_manager import StoreManagerService

            StoreManagerService().sync_from_admin(self.instance, self.cleaned_data)

    def _clean_optional_json_object(self, field_name: str):
        raw = (self.cleaned_data.get(field_name) or "").strip()
        if not raw:
            return ""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"JSON نامعتبر است: {exc.msg}") from exc
        if not isinstance(parsed, dict):
            raise forms.ValidationError("مقدار JSON باید یک آبجکت باشد.")
        return json.dumps(parsed, ensure_ascii=False, indent=2)

    def _clean_optional_json_array(self, field_name: str):
        raw = (self.cleaned_data.get(field_name) or "").strip()
        if not raw:
            return ""
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"JSON نامعتبر است: {exc.msg}") from exc
        if not isinstance(parsed, list):
            raise forms.ValidationError("مقدار JSON باید یک آرایه باشد.")
        return json.dumps(parsed, ensure_ascii=False, indent=2)

    def clean_idpay_json(self):
        return self._clean_optional_json_object("idpay_json")

    def clean_mellat_json(self):
        return self._clean_optional_json_object("mellat_json")

    def clean_pasargad_json(self):
        return self._clean_optional_json_object("pasargad_json")

    def clean_sina_json(self):
        return self._clean_optional_json_object("sina_json")

    def clean_ship_post_json(self):
        return self._clean_optional_json_object("ship_post_json")

    def clean_ship_tipax_json(self):
        return self._clean_optional_json_object("ship_tipax_json")

    def clean_ship_peyk_json(self):
        return self._clean_optional_json_object("ship_peyk_json")

    def clean_theme_hero_slides_json(self):
        return self._clean_optional_json_array("theme_hero_slides_json")

    def clean_store_manager_phone(self):
        raw = (self.cleaned_data.get("store_manager_phone") or "").strip()
        if not raw:
            return ""
        phone = UserManager.normalize_phone(raw)
        if not re.fullmatch(r"09\d{9}", phone):
            raise forms.ValidationError("شماره موبایل معتبر نیست (مثلاً ۰۹۱۲۱۲۳۴۵۶۷).")
        return phone

    def clean_seo_google_site_verification(self):
        raw = (self.cleaned_data.get("seo_google_site_verification") or "").strip()
        if not raw:
            return ""
        from tenants.services.seo import SeoError, parse_google_verification

        try:
            parse_google_verification(raw)
        except SeoError as exc:
            raise forms.ValidationError(str(exc)) from exc
        return raw

    def clean(self):
        cleaned = super().clean()
        if (cleaned.get("sms_otp_provider") or "console_sms") != "payamak":
            return cleaned
        if not (cleaned.get("sms_payamak_username") or "").strip():
            self.add_error("sms_payamak_username", "برای ملی‌پیامک نام کاربری لازم است.")
        if not (cleaned.get("sms_payamak_body_id") or "").strip():
            self.add_error("sms_payamak_body_id", "شناسه پترن (bodyId) لازم است.")
        password = (cleaned.get("sms_payamak_password") or "").strip()
        if not password and self.instance and self.instance.pk:
            existing = StoreConfigService()._group_map(self.instance, "notifications")
            sms = existing.get("sms") if isinstance(existing.get("sms"), dict) else {}
            password = str(sms.get("password") or "").strip()
        if not password:
            self.add_error("sms_payamak_password", "رمز عبور ملی‌پیامک لازم است.")
        return cleaned
