/**
 * Shared storefront toast notifications.
 * API: ShopToast.show(message, { type: 'success'|'error'|'info', duration })
 */
(function (global) {
    const DEFAULT_DURATION = 3200;
    const HOST_ID = "shop-toast-host";
    const STYLE_ID = "shop-toast-styles";

    const TYPE_ROLE = {
        success: "status",
        info: "status",
        error: "alert",
    };

    function ensureStyles() {
        if (document.getElementById(STYLE_ID)) return;
        const style = document.createElement("style");
        style.id = STYLE_ID;
        style.textContent = [
            "#" + HOST_ID + "{",
            "position:fixed;z-index:9999;inset-inline-end:1rem;bottom:1.25rem;",
            "display:flex;flex-direction:column;gap:0.5rem;",
            "max-width:min(92vw,22rem);pointer-events:none;",
            "}",
            ".ps-toast{",
            "pointer-events:auto;padding:0.75rem 1rem;border-radius:0.75rem;",
            "background:#111827;color:#fff;font-size:0.9rem;line-height:1.45;",
            "box-shadow:0 10px 30px rgba(15,23,42,.22);",
            "opacity:0;transform:translateY(0.5rem);",
            "transition:opacity .2s ease,transform .2s ease;",
            "}",
            ".ps-toast.is-visible{opacity:1;transform:translateY(0);}",
            ".ps-toast--success{background:#059669;}",
            ".ps-toast--error{background:#b91c1c;}",
            ".ps-toast--info{background:#111827;}",
            "@media (prefers-reduced-motion:reduce){",
            ".ps-toast{transition:none;}",
            "}",
        ].join("");
        document.head.appendChild(style);
    }

    function ensureHost() {
        ensureStyles();
        let host = document.getElementById(HOST_ID);
        if (!host) {
            host = document.createElement("div");
            host.id = HOST_ID;
            host.className = "ps-toast-host";
            host.setAttribute("aria-live", "polite");
            host.setAttribute("aria-relevant", "additions");
            document.body.appendChild(host);
        }
        return host;
    }

    function show(message, options) {
        const text = String(message || "").trim();
        if (!text) return;

        const opts = options || {};
        const type = ["success", "error", "info"].includes(opts.type) ? opts.type : "info";
        const duration = Number(opts.duration);
        const hideAfter = Number.isFinite(duration) && duration > 0 ? duration : DEFAULT_DURATION;

        const host = ensureHost();
        const el = document.createElement("div");
        el.className = "ps-toast ps-toast--" + type;
        el.setAttribute("role", TYPE_ROLE[type] || "status");
        if (type === "error") el.setAttribute("aria-live", "assertive");
        el.textContent = text;
        host.appendChild(el);

        requestAnimationFrame(() => {
            el.classList.add("is-visible");
        });

        const hideTimer = setTimeout(() => {
            el.classList.remove("is-visible");
            setTimeout(() => {
                el.remove();
                if (host.childElementCount === 0) host.remove();
            }, 220);
        }, hideAfter);

        el.addEventListener("click", () => {
            clearTimeout(hideTimer);
            el.classList.remove("is-visible");
            setTimeout(() => el.remove(), 180);
        });
    }

    global.ShopToast = {
        show: show,
        success: function (message, options) {
            show(message, Object.assign({}, options, { type: "success" }));
        },
        error: function (message, options) {
            show(message, Object.assign({}, options, { type: "error" }));
        },
        info: function (message, options) {
            show(message, Object.assign({}, options, { type: "info" }));
        },
    };
})(typeof window !== "undefined" ? window : this);
