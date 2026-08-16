"""Admin form for unified store configuration."""

from __future__ import annotations

import re

from django import forms

from accounts.managers import UserManager
from payments.enums import GatewayType
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

    shipping_origin_city = forms.CharField(
        required=False,
        label="شهر مبدا",
        widget=UnfoldAdminTextInputWidget(),
    )
    shipping_origin_province = forms.CharField(
        required=False,
        label="استان مبدا",
        widget=UnfoldAdminTextInputWidget(),
    )
    shipping_free_threshold = forms.DecimalField(
        required=False,
        label="آستانه ارسال رایگان",
        min_value=0,
        decimal_places=0,
        max_digits=12,
        widget=UnfoldAdminTextInputWidget(attrs={"dir": "ltr", "placeholder": "0"}),
    )
    shipping_default_provider = forms.CharField(
        required=False,
        label="ارائه‌دهنده پیش‌فرض",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "post / tipax", "dir": "ltr"}),
    )

    storage_driver = forms.CharField(
        required=False,
        label="درایور ذخیره‌سازی",
        widget=UnfoldAdminTextInputWidget(attrs={"placeholder": "local", "dir": "ltr"}),
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
