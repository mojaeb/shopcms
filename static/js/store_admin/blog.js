(function () {
    const api = window.StoreAdminApi;
    if (!api || !api.requireAuth()) return;

    const tbody = document.getElementById("blog-tbody");
    const host = document.getElementById("blog-table-host");
    const q = document.getElementById("blog-q");
    let items = [];

    function render() {
        const term = (q.value || "").trim().toLowerCase();
        const filtered = items.filter(function (p) {
            if (!term) return true;
            return (p.title || "").toLowerCase().includes(term) || (p.slug || "").toLowerCase().includes(term);
        });
        if (!filtered.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="sa-muted">مقاله‌ای یافت نشد.</td></tr>';
            return;
        }
        tbody.innerHTML = filtered.map(function (p) {
            return (
                "<tr>" +
                "<td>" + (p.title || "") + "</td>" +
                "<td>" + (p.category || "—") + "</td>" +
                "<td>" + (p.is_published ? "منتشر" : "پیش‌نویس") + "</td>" +
                '<td class="sa-row-actions">' +
                '<a class="sa-btn sa-btn-ghost sa-btn-sm" href="/manage/blog/' + p.id + '/edit/">ویرایش</a> ' +
                '<button type="button" class="sa-btn sa-btn-danger sa-btn-sm js-del" data-id="' + p.id + '">حذف</button>' +
                "</td></tr>"
            );
        }).join("");
    }

    function load() {
        api.setPageLoading(host, true);
        api.apiFetch("/api/v1/store-admin/blog/posts").then(function (res) {
            api.setPageLoading(host, false);
            if (!res.ok) {
                tbody.innerHTML = '<tr><td colspan="4" class="sa-muted">خطا در بارگذاری (پلاگین وبلاگ؟)</td></tr>';
                api.flash(res.data?.detail || "خطا", true);
                return;
            }
            items = api.unwrapList(res.data);
            render();
        });
    }

    tbody.addEventListener("click", function (e) {
        const btn = e.target.closest(".js-del");
        if (!btn) return;
        const id = btn.getAttribute("data-id");
        if (!window.confirm("این مقاله حذف شود؟")) return;
        api.setBusy(btn, true, "حذف...");
        api.apiFetch("/api/v1/store-admin/blog/posts/" + id, { method: "DELETE" }).then(function (res) {
            if (!res.ok) {
                api.setBusy(btn, false);
                api.flash(res.data?.detail || "حذف ناموفق", true);
                return;
            }
            api.flash("مقاله حذف شد");
            load();
        });
    });

    q.addEventListener("input", render);
    load();
})();
