(function () {
    const root = document.getElementById("sa-products");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/products/")) return;

    const wrap = document.getElementById("products-table-wrap");
    const searchInput = document.getElementById("product-search");
    const pager = document.getElementById("products-pager");
    const pageLabel = document.getElementById("products-page-label");
    const prevBtn = document.getElementById("products-prev");
    const nextBtn = document.getElementById("products-next");
    const PAGE_SIZE = 20;
    let page = 1;
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

    function updatePager(count) {
        const total = Math.max(0, Number(count) || 0);
        const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
        if (page > pages) page = pages;
        const show = total > PAGE_SIZE;
        if (pager) pager.hidden = !show;
        if (prevBtn) prevBtn.disabled = page <= 1;
        if (nextBtn) nextBtn.disabled = page >= pages;
        if (!pageLabel) return;
        const start = total ? (page - 1) * PAGE_SIZE + 1 : 0;
        const end = Math.min(page * PAGE_SIZE, total);
        pageLabel.textContent =
            "صفحه " +
            api.formatNumber(page) +
            " از " +
            api.formatNumber(pages) +
            " · " +
            api.formatNumber(start) +
            "–" +
            api.formatNumber(end) +
            " از " +
            api.formatNumber(total);
    }

    function loadProducts() {
        const q = (searchInput.value || "").trim();
        const params = new URLSearchParams();
        params.set("page", String(page));
        if (q) params.set("search", q);
        api.setPageLoading(wrap, true);
        api.apiFetch("/api/v1/store-admin/products/?" + params.toString()).then(function ({ ok, data }) {
            api.setPageLoading(wrap, false);
            if (!ok) {
                wrap.innerHTML = '<div class="sa-empty">خطا در بارگذاری محصولات</div>';
                if (pager) pager.hidden = true;
                return;
            }
            const items = api.unwrapList(data);
            const count = data && typeof data.count === "number" ? data.count : items.length;
            const pages = Math.max(1, Math.ceil(count / PAGE_SIZE));
            if (page > pages) {
                page = pages;
                loadProducts();
                return;
            }
            renderTable(items);
            updatePager(count);
        });
    }

    searchInput.addEventListener("input", function () {
        clearTimeout(searchTimer);
        page = 1;
        searchTimer = setTimeout(loadProducts, 300);
    });

    if (prevBtn) {
        prevBtn.addEventListener("click", function () {
            if (page <= 1) return;
            page -= 1;
            loadProducts();
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener("click", function () {
            page += 1;
            loadProducts();
        });
    }

    loadProducts();
})();
