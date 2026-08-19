(function () {
    const root = document.getElementById("sa-dashboard");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/")) return;

    const STATUS_LABELS = {
        active: "فعال",
        inactive: "غیرفعال",
        suspended: "معلق",
        pending: "در انتظار",
        draft: "پیش‌نویس",
    };

    const TYPE_LABELS = {
        retail: "خرده‌فروشی",
        wholesale: "عمده",
        digital: "دیجیتال",
        hybrid: "ترکیبی",
        marketplace: "مارکت‌پلیس",
    };

    function labelOf(map, key, fallback) {
        if (!key) return fallback || "—";
        return map[String(key).toLowerCase()] || key || fallback || "—";
    }

    function statusClass(status) {
        const s = String(status || "").toLowerCase();
        if (s === "active") return "sa-badge-ok";
        if (s === "suspended" || s === "inactive") return "sa-badge-warn";
        return "sa-badge-muted";
    }

    function kpiCard(item) {
        const tone = item.tone ? " sa-dash-kpi--" + item.tone : "";
        const hint = item.hint
            ? '<span class="sa-dash-kpi-hint">' + api.escapeHtml(item.hint) + "</span>"
            : "";
        const inner =
            '<span class="sa-dash-kpi-label">' +
            api.escapeHtml(item.label) +
            "</span>" +
            '<span class="sa-dash-kpi-value">' +
            item.value +
            "</span>" +
            hint;
        if (item.href) {
            return (
                '<a class="sa-dash-kpi' +
                tone +
                '" href="' +
                api.escapeHtml(item.href) +
                '">' +
                inner +
                '<span class="sa-dash-kpi-go" aria-hidden="true">←</span></a>'
            );
        }
        return '<div class="sa-dash-kpi' + tone + '">' + inner + "</div>";
    }

    function shortcut(item) {
        return (
            '<a class="sa-dash-shortcut" href="' +
            api.escapeHtml(item.href) +
            '">' +
            '<span class="sa-dash-shortcut-title">' +
            api.escapeHtml(item.title) +
            "</span>" +
            '<span class="sa-dash-shortcut-desc">' +
            api.escapeHtml(item.desc) +
            "</span></a>"
        );
    }

    function attentionItem(item) {
        return (
            '<a class="sa-dash-alert" href="' +
            api.escapeHtml(item.href) +
            '">' +
            '<span class="sa-dash-alert-count">' +
            api.formatNumber(item.count) +
            "</span>" +
            '<span class="sa-dash-alert-body">' +
            '<strong>' +
            api.escapeHtml(item.title) +
            "</strong>" +
            '<span>' +
            api.escapeHtml(item.desc) +
            "</span></span>" +
            '<span class="sa-dash-alert-cta">مشاهده</span></a>'
        );
    }

    api.setPageLoading(root, true);
    api.apiFetch("/api/v1/store-admin/dashboard").then(function ({ ok, data }) {
        api.setPageLoading(root, false);
        if (!ok) {
            root.innerHTML =
                '<div class="sa-empty">خطا در بارگذاری داشبورد: ' +
                api.escapeHtml((data && data.detail) || "") +
                "</div>";
            return;
        }

        const pendingOrders = Number(data.pending_orders || 0);
        const pendingComments = Number(data.pending_comments || 0);
        const currency = data.currency || "تومان";
        const statusLabel = labelOf(STATUS_LABELS, data.status, data.status);
        const typeLabel = labelOf(TYPE_LABELS, data.store_type, data.store_type);

        const alerts = [];
        if (pendingOrders > 0) {
            alerts.push({
                count: pendingOrders,
                title: "سفارش در انتظار رسیدگی",
                desc: "نیاز به تایید، آماده‌سازی یا ارسال دارند.",
                href: "/manage/orders/",
            });
        }
        if (pendingComments > 0) {
            alerts.push({
                count: pendingComments,
                title: "نظر منتظر تایید",
                desc: "نظرات محصول و وبلاگ آماده moderation هستند.",
                href: "/manage/comments/",
            });
        }

        const todayKpis = [
            {
                label: "سفارش امروز",
                value: api.formatNumber(data.orders_today || 0),
                href: "/manage/orders/",
                tone: Number(data.orders_today) > 0 ? "accent" : "",
            },
            {
                label: "مشتری جدید امروز",
                value: api.formatNumber(data.new_customers_today || 0),
            },
            {
                label: "درآمد کل",
                value: api.formatNumber(data.total_revenue || 0),
                hint: currency,
                tone: "money",
            },
        ];

        const catalogKpis = [
            {
                label: "محصولات",
                value: api.formatNumber(data.total_products || 0),
                href: "/manage/products/",
            },
            {
                label: "کل سفارش‌ها",
                value: api.formatNumber(data.total_orders || 0),
                href: "/manage/orders/",
            },
            {
                label: "مشتریان فعال",
                value: api.formatNumber(data.active_customers || 0),
                hint: "از " + api.formatNumber(data.total_customers || 0) + " عضو",
            },
            {
                label: "تیم فروشگاه",
                value: api.formatNumber(data.total_staff || 0),
            },
        ];

        const shortcuts = [
            {
                title: "محصول جدید",
                desc: "افزودن کالا به کاتالوگ",
                href: "/manage/products/new/",
            },
            {
                title: "سفارش‌ها",
                desc: "پیگیری و تغییر وضعیت",
                href: "/manage/orders/",
            },
            {
                title: "نظرات",
                desc: "تایید یا رد بازخوردها",
                href: "/manage/comments/",
            },
            {
                title: "رسانه",
                desc: "آپلود تصویر و فایل",
                href: "/manage/files/",
            },
            {
                title: "صفحات",
                desc: "درباره ما، تماس و محتوا",
                href: "/manage/pages/",
            },
            {
                title: "تخفیف و کارت هدیه",
                desc: "کد تخفیف و موجودی کارت",
                href: "/manage/discounts/",
            },
            {
                title: "تنظیمات",
                desc: "ارز، تم و هویت فروشگاه",
                href: "/manage/settings/",
            },
        ];

        const metaBits = [
            "ارز: " + currency,
            data.tax_enabled ? "مالیات فعال" : "مالیات غیرفعال",
            api.formatNumber(data.enabled_plugins || 0) + " افزونه فعال",
        ];

        root.innerHTML =
            '<div class="sa-dash">' +
            '<header class="sa-dash-hero">' +
            '<div class="sa-dash-hero-copy">' +
            '<p class="sa-dash-kicker">خلاصه عملیات فروشگاه</p>' +
            "<h2>" +
            api.escapeHtml(data.store_name || "فروشگاه") +
            "</h2>" +
            '<p class="sa-dash-hero-sub">' +
            '<span class="sa-badge ' +
            statusClass(data.status) +
            '">' +
            api.escapeHtml(statusLabel) +
            "</span>" +
            '<span class="sa-dash-dot" aria-hidden="true"></span>' +
            "<span>" +
            api.escapeHtml(typeLabel) +
            "</span>" +
            '<span class="sa-dash-dot" aria-hidden="true"></span>' +
            '<span dir="ltr">' +
            api.escapeHtml(data.store_slug || "") +
            "</span></p>" +
            '<p class="sa-dash-meta">' +
            metaBits.map(function (b) {
                return "<span>" + api.escapeHtml(b) + "</span>";
            }).join("") +
            "</p></div>" +
            '<div class="sa-dash-hero-actions">' +
            '<a class="sa-btn" href="/manage/products/new/">محصول جدید</a>' +
            '<a class="sa-btn sa-btn-ghost" href="/" target="_blank" rel="noopener">مشاهده فروشگاه</a>' +
            "</div></header>" +
            (alerts.length
                ? '<section class="sa-dash-section" aria-label="نیاز به رسیدگی">' +
                  '<div class="sa-dash-section-head">' +
                  "<h3>نیاز به رسیدگی</h3>" +
                  "<p>مواردی که الان باید بررسی کنید.</p></div>" +
                  '<div class="sa-dash-alerts">' +
                  alerts.map(attentionItem).join("") +
                  "</div></section>"
                : '<section class="sa-dash-calm" aria-live="polite">' +
                  "<strong>همه‌چیز آرام است.</strong>" +
                  "<span>سفارش یا نظر معلقی برای رسیدگی فوری وجود ندارد.</span></section>") +
            '<section class="sa-dash-section">' +
            '<div class="sa-dash-section-head">' +
            "<h3>امروز و درآمد</h3>" +
            "<p>نبض روزانه فروشگاه.</p></div>" +
            '<div class="sa-dash-kpis sa-dash-kpis--3">' +
            todayKpis.map(kpiCard).join("") +
            "</div></section>" +
            '<section class="sa-dash-section">' +
            '<div class="sa-dash-section-head">' +
            "<h3>کاتالوگ و مخاطب</h3>" +
            "<p>وضعیت کلی محصولات، سفارش‌ها و مشتریان.</p></div>" +
            '<div class="sa-dash-kpis">' +
            catalogKpis.map(kpiCard).join("") +
            "</div></section>" +
            '<section class="sa-dash-section">' +
            '<div class="sa-dash-section-head">' +
            "<h3>دسترسی سریع</h3>" +
            "<p>میان‌بر به کارهای پرتکرار.</p></div>" +
            '<div class="sa-dash-shortcuts">' +
            shortcuts.map(shortcut).join("") +
            "</div></section></div>";
    });
})();
