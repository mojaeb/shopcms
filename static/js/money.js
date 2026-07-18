/**
 * Shared money formatting: thousand separators + toman SVG (instead of IRR).
 */
(function (global) {
    const TOMAN_CODES = new Set(["IRR", "IRT", "TOMAN", "TMN", "تومان"]);

    const TOMAN_SVG =
        '<svg class="currency-toman" width="16" height="16" aria-hidden="true" focusable="false">' +
        '<use href="#toman" xlink:href="#toman"></use></svg>';

    function formatAmount(value) {
        const n = Number(value || 0);
        if (Number.isNaN(n)) return String(value ?? "0");
        return Math.round(n) === n
            ? n.toLocaleString("en-US")
            : n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function isToman(currency) {
        if (!currency) return true;
        const code = String(currency).trim().toUpperCase();
        return TOMAN_CODES.has(code) || TOMAN_CODES.has(String(currency).trim());
    }

    function currencySuffix(currency) {
        if (isToman(currency)) return TOMAN_SVG;
        const cur = String(currency || "").trim();
        return cur ? ` <span class="currency-code">${cur}</span>` : "";
    }

    function formatMoney(value, currency) {
        return formatAmount(value) + currencySuffix(currency);
    }

    global.ShopMoney = {
        formatAmount,
        formatMoney,
        isToman,
        TOMAN_SVG,
    };
})(typeof window !== "undefined" ? window : this);
