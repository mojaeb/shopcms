(function () {
    const root = document.getElementById("sa-dashboard");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/")) return;

    api.apiFetch("/api/v1/store-admin/dashboard").then(function ({ ok, data }) {
        if (!ok) {
            root.innerHTML = '<div class="sa-empty">خطا در بارگذاری داشبورد: ' + api.escapeHtml(data.detail || "") + "</div>";
            return;
        }

        const stats = [
            { label: "محصولات", value: data.total_products },
            { label: "سفارشات", value: data.total_orders },
            { label: "در انتظار", value: data.pending_orders },
            { label: "درآمد", value: api.formatNumber(data.total_revenue) + " " + api.escapeHtml(data.currency || "") },
            { label: "مشتریان", value: data.total_customers },
            { label: "سفارش امروز", value: data.orders_today },
            { label: "مشتری جدید امروز", value: data.new_customers_today },
            { label: "افزونه‌های فعال", value: data.enabled_plugins },
        ];

        root.innerHTML =
            '<div class="sa-card" style="margin-bottom:1.25rem;">' +
            "<p><strong>" +
            api.escapeHtml(data.store_name) +
            "</strong> · " +
            api.escapeHtml(data.store_type) +
            ' · <span class="sa-badge sa-badge-ok">' +
            api.escapeHtml(data.status) +
            "</span></p>" +
            '<p class="sa-muted" style="margin-top:0.35rem;">ارز: ' +
            api.escapeHtml(data.currency) +
            (data.tax_enabled ? " · مالیات فعال" : "") +
            "</p>" +
            "</div>" +
            '<div class="sa-stats">' +
            stats
                .map(function (s) {
                    return (
                        '<div class="sa-stat"><div class="label">' +
                        s.label +
                        '</div><div class="value">' +
                        s.value +
                        "</div></div>"
                    );
                })
                .join("") +
            "</div>";
    });
})();
