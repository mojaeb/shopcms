(function () {
    const api = window.StoreAdminApi;
    if (!api) return;

    const listRoot = document.getElementById("sa-orders");
    const detailRoot = document.getElementById("sa-order-detail");

    function statusBadge(label) {
        return '<span class="sa-badge">' + api.escapeHtml(label || "") + "</span>";
    }

    if (listRoot) {
        if (!api.requireAuth("/manage/orders/")) return;
        const wrap = document.getElementById("orders-table-wrap");
        const filter = document.getElementById("order-status-filter");
        let statuses = [];

        function loadStatuses() {
            return api.apiFetch("/api/v1/store-admin/orders/meta/statuses").then(function ({ ok, data }) {
                statuses = ok ? api.unwrapList(data) : [];
                filter.innerHTML = '<option value="">همه وضعیت‌ها</option>';
                statuses.forEach(function (s) {
                    const opt = document.createElement("option");
                    opt.value = s.value;
                    opt.textContent = s.label;
                    filter.appendChild(opt);
                });
            });
        }

        function renderOrders(items) {
            if (!items.length) {
                wrap.innerHTML = '<div class="sa-empty sa-card">سفارشی یافت نشد.</div>';
                return;
            }
            wrap.innerHTML =
                '<div class="sa-table-wrap"><table class="sa-table"><thead><tr>' +
                "<th>شماره</th><th>مشتری</th><th>وضعیت</th><th>مبلغ</th><th>تاریخ</th><th></th>" +
                "</tr></thead><tbody>" +
                items
                    .map(function (o) {
                        const phone = (o.user && (o.user.phone || o.user.full_name)) || "—";
                        return (
                            "<tr>" +
                            "<td><strong>" +
                            api.escapeHtml(o.order_number) +
                            "</strong></td>" +
                            "<td>" +
                            api.escapeHtml(phone) +
                            "</td>" +
                            "<td>" +
                            statusBadge(o.status_label || o.status) +
                            "</td>" +
                            "<td>" +
                            api.formatNumber(o.total) +
                            "</td>" +
                            "<td>" +
                            api.escapeHtml((o.created_at || "").replace("T", " ").slice(0, 16)) +
                            "</td>" +
                            '<td><a class="sa-btn sa-btn-ghost sa-btn-sm" href="/manage/orders/' +
                            o.id +
                            '/">جزئیات</a></td>' +
                            "</tr>"
                        );
                    })
                    .join("") +
                "</tbody></table></div>";
        }

        function loadOrders() {
            const status = filter.value;
            const qs = status ? "?status=" + encodeURIComponent(status) : "";
            wrap.innerHTML = '<div class="sa-loading">در حال بارگذاری...</div>';
            api.apiFetch("/api/v1/store-admin/orders/" + qs).then(function ({ ok, data }) {
                if (!ok) {
                    wrap.innerHTML = '<div class="sa-empty">خطا در بارگذاری سفارشات</div>';
                    return;
                }
                renderOrders(api.unwrapList(data));
            });
        }

        filter.addEventListener("change", loadOrders);
        document.getElementById("orders-refresh").addEventListener("click", loadOrders);
        loadStatuses().then(loadOrders);
        return;
    }

    if (!detailRoot) return;
    const orderId = detailRoot.dataset.orderId;
    if (!api.requireAuth("/manage/orders/" + orderId + "/")) return;

    let statuses = [];

    function loadStatuses() {
        return api.apiFetch("/api/v1/store-admin/orders/meta/statuses").then(function ({ ok, data }) {
            statuses = ok ? api.unwrapList(data) : [];
        });
    }

    function renderDetail(order) {
        const itemsHtml = (order.items || [])
            .map(function (it) {
                return (
                    "<tr><td>" +
                    api.escapeHtml(it.name || it.product_name || it.title || "—") +
                    "</td><td>" +
                    api.formatNumber(it.quantity) +
                    "</td><td>" +
                    api.formatNumber(it.unit_price || it.price || 0) +
                    "</td><td>" +
                    api.formatNumber(it.line_total || it.total || 0) +
                    "</td></tr>"
                );
            })
            .join("");

        const statusOptions = statuses
            .map(function (s) {
                const selected = s.value === order.status ? " selected" : "";
                return (
                    '<option value="' +
                    api.escapeHtml(s.value) +
                    '"' +
                    selected +
                    ">" +
                    api.escapeHtml(s.label) +
                    "</option>"
                );
            })
            .join("");

        const shipment = order.shipment || {};

        detailRoot.innerHTML =
            '<p class="sa-back"><a href="/manage/orders/">← بازگشت به لیست</a></p>' +
            '<div class="sa-grid-2">' +
            '<div class="sa-card">' +
            '<h2 style="margin-bottom:0.75rem;">سفارش ' +
            api.escapeHtml(order.order_number) +
            "</h2>" +
            "<p>وضعیت: " +
            statusBadge(order.status_label || order.status) +
            "</p>" +
            '<p class="sa-muted" style="margin-top:0.5rem;">تاریخ: ' +
            api.escapeHtml((order.created_at || "").replace("T", " ").slice(0, 19)) +
            "</p>" +
            '<p style="margin-top:0.5rem;">مبلغ کل: <strong>' +
            api.formatNumber(order.total) +
            "</strong></p>" +
            (order.customer_note
                ? '<p class="sa-muted" style="margin-top:0.75rem;">یادداشت مشتری: ' +
                  api.escapeHtml(order.customer_note) +
                  "</p>"
                : "") +
            "</div>" +
            '<div class="sa-card">' +
            '<h3 style="margin-bottom:0.75rem;">تغییر وضعیت</h3>' +
            '<label>وضعیت جدید<select id="order-status" class="sa-input">' +
            statusOptions +
            "</select></label>" +
            '<label style="margin-top:0.75rem;display:block;">یادداشت<input type="text" id="order-note" class="sa-input" placeholder="اختیاری"></label>' +
            '<button type="button" class="sa-btn" id="save-status" style="margin-top:0.75rem;">ذخیره وضعیت</button>' +
            '<h3 style="margin:1.25rem 0 0.75rem;">ارسال</h3>' +
            '<label>کد رهگیری<input type="text" id="tracking-code" class="sa-input" value="' +
            api.escapeHtml(shipment.tracking_code || "") +
            '"></label>' +
            '<label style="margin-top:0.75rem;display:block;">حامل<input type="text" id="carrier" class="sa-input" value="' +
            api.escapeHtml(shipment.carrier || "") +
            '"></label>' +
            '<button type="button" class="sa-btn sa-btn-ghost" id="save-shipment" style="margin-top:0.75rem;">ذخیره ارسال</button>' +
            "</div></div>" +
            '<div class="sa-card" style="margin-top:1rem;">' +
            '<h3 style="margin-bottom:0.75rem;">اقلام</h3>' +
            '<div class="sa-table-wrap"><table class="sa-table"><thead><tr><th>محصول</th><th>تعداد</th><th>قیمت</th><th>جمع</th></tr></thead><tbody>' +
            (itemsHtml || '<tr><td colspan="4" class="sa-muted">موردی نیست</td></tr>') +
            "</tbody></table></div></div>";

        document.getElementById("save-status").addEventListener("click", function () {
            api.apiFetch("/api/v1/store-admin/orders/" + orderId + "/status", {
                method: "PUT",
                body: JSON.stringify({
                    status: document.getElementById("order-status").value,
                    note: document.getElementById("order-note").value.trim(),
                }),
            }).then(function ({ ok, data }) {
                if (!ok) {
                    api.flash(data.detail || "به‌روزرسانی وضعیت ناموفق", true);
                    return;
                }
                api.flash("وضعیت به‌روز شد");
                loadDetail();
            });
        });

        document.getElementById("save-shipment").addEventListener("click", function () {
            api.apiFetch("/api/v1/store-admin/orders/" + orderId + "/shipment", {
                method: "PUT",
                body: JSON.stringify({
                    tracking_code: document.getElementById("tracking-code").value.trim(),
                    carrier: document.getElementById("carrier").value.trim(),
                }),
            }).then(function ({ ok, data }) {
                if (!ok) {
                    api.flash(data.detail || "ذخیره ارسال ناموفق", true);
                    return;
                }
                api.flash("اطلاعات ارسال ذخیره شد");
                loadDetail();
            });
        });
    }

    function loadDetail() {
        api.apiFetch("/api/v1/store-admin/orders/" + orderId).then(function ({ ok, data }) {
            if (!ok) {
                detailRoot.innerHTML =
                    '<p class="sa-back"><a href="/manage/orders/">← بازگشت</a></p><div class="sa-empty">سفارش یافت نشد</div>';
                return;
            }
            renderDetail(data);
        });
    }

    loadStatuses().then(loadDetail);
})();
