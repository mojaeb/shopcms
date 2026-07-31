(function () {
    const root = document.getElementById("sa-comments");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/comments/")) return;

    const wrap = document.getElementById("comments-table-wrap");
    const statusFilter = document.getElementById("comments-status-filter");
    const sourceFilter = document.getElementById("comments-source-filter");
    const refreshBtn = document.getElementById("comments-refresh");
    const badge = document.getElementById("comments-pending-badge");

    function formatDate(iso) {
        if (!iso) return "—";
        try {
            return new Date(iso).toLocaleString("fa-IR");
        } catch (_) {
            return iso;
        }
    }

    function statusBadge(status) {
        if (status === "approved") return '<span class="sa-badge sa-badge-ok">تایید شده</span>';
        if (status === "rejected") return '<span class="sa-badge sa-badge-muted">رد شده</span>';
        return '<span class="sa-badge sa-badge-warn">در انتظار</span>';
    }

    function moderate(source, id, status) {
        const url =
            source === "blog"
                ? "/api/v1/store-admin/blog/comments/" + id + "/status"
                : "/api/v1/store-admin/comments/" + id + "/status";
        return api.apiFetch(url, {
            method: "PUT",
            body: JSON.stringify({ status: status }),
        });
    }

    function renderRows(items) {
        if (!items.length) {
            wrap.innerHTML = '<div class="sa-empty">نظری با این فیلتر پیدا نشد.</div>';
            return;
        }
        wrap.innerHTML =
            '<div class="sa-table-wrap"><table class="sa-table"><thead><tr>' +
            "<th>منبع</th><th>موضوع</th><th>کاربر</th><th>متن</th><th>وضعیت</th><th>تاریخ</th><th></th>" +
            "</tr></thead><tbody>" +
            items
                .map(function (c) {
                    const sourceLabel = c.source === "blog" ? "وبلاگ" : "محصول";
                    const topic =
                        c.source === "blog"
                            ? '<a href="/blog/' +
                              api.escapeHtml(c.post_slug || "") +
                              '/" target="_blank" rel="noopener">' +
                              api.escapeHtml(c.post_title || "—") +
                              "</a>"
                            : '<a href="/product/' +
                              api.escapeHtml(c.product_slug || "") +
                              '/" target="_blank" rel="noopener">' +
                              api.escapeHtml(c.product_name || "—") +
                              "</a>";
                    const userName =
                        typeof c.user === "string"
                            ? c.user
                            : (c.user && (c.user.full_name || c.user.phone)) || "—";
                    const replyNote = c.parent_id ? ' <span class="sa-muted">(پاسخ)</span>' : "";
                    const rating =
                        c.rating != null
                            ? ' <span class="sa-muted">★ ' + api.escapeHtml(String(c.rating)) + "</span>"
                            : "";
                    const actions =
                        c.status === "pending"
                            ? '<button type="button" class="sa-btn sa-btn-sm" data-act="approve" data-source="' +
                              c.source +
                              '" data-id="' +
                              c.id +
                              '">تایید</button> ' +
                              '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm" data-act="reject" data-source="' +
                              c.source +
                              '" data-id="' +
                              c.id +
                              '">رد</button>'
                            : c.status === "approved"
                              ? '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm" data-act="reject" data-source="' +
                                c.source +
                                '" data-id="' +
                                c.id +
                                '">رد</button>'
                              : '<button type="button" class="sa-btn sa-btn-sm" data-act="approve" data-source="' +
                                c.source +
                                '" data-id="' +
                                c.id +
                                '">تایید</button>';

                    return (
                        "<tr>" +
                        "<td>" +
                        sourceLabel +
                        replyNote +
                        "</td>" +
                        "<td>" +
                        topic +
                        rating +
                        "</td>" +
                        "<td>" +
                        api.escapeHtml(userName) +
                        "</td>" +
                        '<td style="max-width:22rem;">' +
                        api.escapeHtml(c.body || "") +
                        "</td>" +
                        "<td>" +
                        statusBadge(c.status) +
                        "</td>" +
                        "<td>" +
                        formatDate(c.created_at) +
                        "</td>" +
                        '<td class="sa-row-actions">' +
                        actions +
                        "</td>" +
                        "</tr>"
                    );
                })
                .join("") +
            "</tbody></table></div>";

        wrap.querySelectorAll("[data-act]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const act = btn.getAttribute("data-act");
                const source = btn.getAttribute("data-source");
                const id = btn.getAttribute("data-id");
                const next = act === "approve" ? "approved" : "rejected";
                api.setBusy(btn, true, act === "approve" ? "تایید..." : "رد...");
                moderate(source, id, next).then(function (res) {
                    if (!res.ok) {
                        api.flash((res.data && res.data.detail) || "خطا در تغییر وضعیت", true);
                        api.setBusy(btn, false);
                        return;
                    }
                    api.flash(next === "approved" ? "نظر تایید شد." : "نظر رد شد.");
                    load();
                });
            });
        });
    }

    function normalizeProduct(c) {
        return Object.assign({}, c, { source: "product" });
    }

    function load() {
        api.setPageLoading(wrap, true);
        const status = statusFilter.value;
        const source = sourceFilter.value;
        const productQs = status ? "?status=" + encodeURIComponent(status) : "";
        const blogQs = status ? "?status=" + encodeURIComponent(status) : "";

        const tasks = [];
        if (source === "all" || source === "product") {
            tasks.push(
                api.apiFetch("/api/v1/store-admin/comments/" + productQs).then(function (res) {
                    if (!res.ok) return [];
                    return api.unwrapList(res.data).map(normalizeProduct);
                })
            );
        } else {
            tasks.push(Promise.resolve([]));
        }
        if (source === "all" || source === "blog") {
            const blogPath = status
                ? "/api/v1/store-admin/blog/comments" + blogQs
                : "/api/v1/store-admin/blog/comments";
            tasks.push(
                api.apiFetch(blogPath).then(function (res) {
                    if (!res.ok) return [];
                    const list = Array.isArray(res.data) ? res.data : api.unwrapList(res.data);
                    return list;
                })
            );
        } else {
            tasks.push(Promise.resolve([]));
        }

        return Promise.all([
            Promise.all(tasks),
            api.apiFetch("/api/v1/store-admin/comments/stats"),
            api.apiFetch("/api/v1/store-admin/blog/comments/pending"),
        ]).then(function (results) {
            api.setPageLoading(wrap, false);
            const lists = results[0];
            const productItems = lists[0] || [];
            const blogItems = lists[1] || [];
            const merged = productItems.concat(blogItems).sort(function (a, b) {
                return String(b.created_at || "").localeCompare(String(a.created_at || ""));
            });
            renderRows(merged);

            let pending = 0;
            if (results[1].ok && results[1].data) pending += Number(results[1].data.pending || 0);
            if (results[2].ok) {
                const blogPending = Array.isArray(results[2].data) ? results[2].data.length : 0;
                pending += blogPending;
            }
            if (badge) {
                if (pending > 0) {
                    badge.hidden = false;
                    badge.textContent = api.formatNumber(pending) + " در انتظار";
                } else {
                    badge.hidden = true;
                }
            }
        });
    }

    statusFilter.addEventListener("change", load);
    sourceFilter.addEventListener("change", load);
    refreshBtn.addEventListener("click", function () {
        api.setBusy(refreshBtn, true, "بارگذاری...");
        load().finally(function () {
            api.setBusy(refreshBtn, false);
        });
    });
    load();
})();
