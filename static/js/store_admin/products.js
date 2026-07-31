(function () {
    const root = document.getElementById("sa-products");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/products/")) return;

    const wrap = document.getElementById("products-table-wrap");
    const searchInput = document.getElementById("product-search");
    let searchTimer = null;

    function statusLabel(status) {
        return { draft: "پیش‌نویس", active: "فعال", inactive: "غیرفعال" }[status] || status || "—";
    }

    function typeLabel(type) {
        return { simple: "ساده", variable: "متغیر", digital: "دیجیتال", subscription: "اشتراک" }[type] || type || "—";
    }

    function statusBadge(status) {
        const cls = status === "active" ? "sa-badge-ok" : status === "draft" ? "sa-badge-warn" : "sa-badge-muted";
        return '<span class="sa-badge ' + cls + '">' + api.escapeHtml(statusLabel(status)) + "</span>";
    }

    function renderTable(items) {
        if (!items.length) {
            wrap.innerHTML =
                '<div class="sa-empty sa-card">محصولی یافت نشد. <a href="/manage/products/new/">محصول جدید بسازید</a></div>';
            return;
        }
        wrap.innerHTML =
            '<div class="sa-table-wrap"><table class="sa-table"><thead><tr>' +
            "<th>نام</th><th>نوع</th><th>قیمت</th><th>وضعیت</th><th>موجودی</th><th></th>" +
            "</tr></thead><tbody>" +
            items
                .map(function (p) {
                    return (
                        "<tr>" +
                        "<td><a href=\"/manage/products/" +
                        p.id +
                        '/edit/"><strong>' +
                        api.escapeHtml(p.name) +
                        '</strong></a><div class="sa-muted sa-text-sm">' +
                        api.escapeHtml(p.slug) +
                        "</div></td>" +
                        "<td>" +
                        api.escapeHtml(typeLabel(p.product_type)) +
                        "</td>" +
                        "<td>" +
                        api.formatNumber(p.base_price) +
                        "</td>" +
                        "<td>" +
                        statusBadge(p.status) +
                        "</td>" +
                        "<td>" +
                        (p.in_stock ? api.formatNumber(p.available) : '<span class="sa-badge">ناموجود</span>') +
                        "</td>" +
                        '<td class="sa-actions">' +
                        '<a href="/manage/products/' +
                        p.id +
                        '/edit/" class="sa-btn sa-btn-ghost sa-btn-sm">ویرایش</a>' +
                        '<button type="button" class="sa-btn sa-btn-danger sa-btn-sm" data-delete="' +
                        p.id +
                        '">حذف</button>' +
                        "</td></tr>"
                    );
                })
                .join("") +
            "</tbody></table></div>";

        wrap.querySelectorAll("[data-delete]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                if (!confirm("این محصول حذف شود؟")) return;
                const id = btn.getAttribute("data-delete");
                api.setBusy(btn, true, "حذف...");
                api.apiFetch("/api/v1/store-admin/products/" + id, { method: "DELETE" }).then(function ({
                    ok,
                    data,
                }) {
                    if (!ok) {
                        api.setBusy(btn, false);
                        api.flash(data.detail || "حذف ناموفق", true);
                        return;
                    }
                    api.flash("محصول حذف شد");
                    loadProducts();
                });
            });
        });
    }

    function loadProducts() {
        const q = (searchInput.value || "").trim();
        const qs = q ? "?search=" + encodeURIComponent(q) : "";
        api.setPageLoading(wrap, true);
        api.apiFetch("/api/v1/store-admin/products/" + qs).then(function ({ ok, data }) {
            api.setPageLoading(wrap, false);
            if (!ok) {
                wrap.innerHTML = '<div class="sa-empty">خطا در بارگذاری محصولات</div>';
                return;
            }
            renderTable(api.unwrapList(data));
        });
    }

    searchInput.addEventListener("input", function () {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(loadProducts, 300);
    });

    loadProducts();
})();
