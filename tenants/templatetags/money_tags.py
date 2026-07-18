"""Currency / money display helpers (toman icon + thousand separators)."""

from decimal import Decimal, InvalidOperation

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

TOMAN_CODES = {"IRR", "IRT", "TOMAN", "TMN", "تومان"}

TOMAN_SVG = (
    '<svg class="currency-toman" width="16" height="16" aria-hidden="true" focusable="false">'
    '<use href="#toman" xlink:href="#toman"></use></svg>'
)


def format_amount(value) -> str:
    if value is None or value == "":
        return "0"
    try:
        amount = Decimal(str(value).replace(",", "").replace("٬", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return str(value)
    if amount == amount.to_integral_value():
        return f"{int(amount):,}"
    return f"{amount:,.2f}"


def is_toman_currency(currency: str | None) -> bool:
    if not currency:
        return True
    code = str(currency).strip().upper()
    return code in TOMAN_CODES or code == "IRR"


def money_html(amount, currency: str | None = None) -> str:
    formatted = format_amount(amount)
    if is_toman_currency(currency):
        return f'<span class="money">{formatted}{TOMAN_SVG}</span>'
    cur = str(currency or "").strip()
    return f'<span class="money">{formatted} <span class="currency-code">{cur}</span></span>'


@register.simple_tag(takes_context=True)
def money(context, amount, currency=None):
    """Render amount with thousand separators + toman icon (or currency code)."""
    store = context.get("store")
    cur = currency
    if cur is None and store is not None:
        cur = getattr(store, "currency", None)
    return mark_safe(money_html(amount, cur))


@register.filter(name="money_format")
def money_format(value) -> str:
    """Format number with thousand separators only (no currency glyph)."""
    return format_amount(value)
