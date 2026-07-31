/**
 * Shared money formatting: Persian digits + toman SVG (instead of IRR).
 * Always wraps amount + currency mark in <span class="money"> so they stay
 * on one line (see .money { white-space: nowrap; inline-flex } in themes).
 */
(function (global) {
    const TOMAN_CODES = new Set(["IRR", "IRT", "TOMAN", "TMN", "تومان"]);

    const TOMAN_SVG =
        '<svg class="currency-toman" width="16" height="16" aria-hidden="true" focusable="false">' +
        '<use href="#toman" xlink:href="#toman"></use></svg>';

    function toPersianDigits(value) {
        return String(value ?? "").replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
    }

    function formatAmount(value) {
        const n = Number(value || 0);
        if (Number.isNaN(n)) return toPersianDigits(value ?? "۰");
        return Math.round(n) === n
            ? n.toLocaleString("fa-IR")
            : n.toLocaleString("fa-IR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function isToman(currency) {
        if (!currency) return true;
        const code = String(currency).trim().toUpperCase();
        return TOMAN_CODES.has(code) || TOMAN_CODES.has(String(currency).trim());
    }

    function currencySuffix(currency) {
        if (isToman(currency)) return TOMAN_SVG;
        const cur = String(currency || "").trim();
        return cur ? `<span class="currency-code">${cur}</span>` : "";
    }

    function formatMoney(value, currency) {
        return (
            '<span class="money">' +
            formatAmount(value) +
            currencySuffix(currency) +
            "</span>"
        );
    }

    function formatMoneyHtml(value, currency) {
        return formatMoney(value, currency);
    }

    global.ShopMoney = {
        formatAmount,
        formatMoney,
        formatMoneyHtml,
        isToman,
        toPersianDigits,
        TOMAN_SVG,
    };
})(typeof window !== "undefined" ? window : this);
