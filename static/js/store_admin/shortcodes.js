(function () {
    const api = window.StoreAdminApi;
    if (!api || !api.requireAuth()) return;

    const tbody = document.getElementById("sc-tbody");
    const host = document.getElementById("sc-table-host");
    const dialog = document.getElementById("sc-dialog");
    const form = document.getElementById("sc-form");
    let items = [];

    function escapeHtml(s) {
        return api.escapeHtml(s);
    }

    function render() {
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="sa-muted">موردی نیست</td></tr>';
            return;
        }
        tbody.innerHTML = items.map(function (sc) {
            const type = sc.is_system ? "سیستمی" : "سفارشی";
            const actions = sc.is_system
                ? '<span class="sa-muted">—</span>'
                : (
                    '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm js-edit" data-id="' + sc.id + '">ویرایش</button> ' +
                    '<button type="button" class="sa-btn sa-btn-danger sa-btn-sm js-del" data-id="' + sc.id + '">حذف</button>'
                );
            return (
                "<tr>" +
                '<td dir="ltr"><code>[' + escapeHtml(sc.name) + "]</code></td>" +
                "<td>" + escapeHtml(sc.label) + "</td>" +
                "<td>" + type + (sc.is_self_closing ? " · بسته" : "") + "</td>" +
                '<td dir="ltr" class="sa-cell-ellipsis">' +
                escapeHtml(sc.example || "") + "</td>" +
                '<td class="sa-row-actions">' + actions + "</td></tr>"
            );
        }).join("");
    }

    function load() {
        api.setPageLoading(host, true);
        api.apiFetch("/api/v1/store-admin/cms/shortcodes").then(function (res) {
            api.setPageLoading(host, false);
            if (!res.ok) {
                tbody.innerHTML = '<tr><td colspan="5" class="sa-muted">خطا</td></tr>';
                return;
            }
            items = Array.isArray(res.data) ? res.data : [];
            render();
        });
    }

    function openCreate() {
        document.getElementById("sc-dialog-title").textContent = "شورت‌کد جدید";
        document.getElementById("sc-id").value = "";
        document.getElementById("sc-name").value = "";
        document.getElementById("sc-name").disabled = false;
        document.getElementById("sc-label").value = "";
        document.getElementById("sc-description").value = "";
        document.getElementById("sc-self-closing").checked = false;
        document.getElementById("sc-template").value = '<div class="my-shortcode">{{content}}</div>';
        document.getElementById("sc-example").value = "[my-shortcode]\nمتن\n[/my-shortcode]";
        document.getElementById("sc-active").checked = true;
        dialog.showModal();
    }

    function openEdit(id) {
        const sc = items.find(function (x) { return String(x.id) === String(id); });
        if (!sc || sc.is_system) return;
        document.getElementById("sc-dialog-title").textContent = "ویرایش شورت‌کد";
        document.getElementById("sc-id").value = sc.id;
        document.getElementById("sc-name").value = sc.name;
        document.getElementById("sc-name").disabled = false;
        document.getElementById("sc-label").value = sc.label || "";
        document.getElementById("sc-description").value = sc.description || "";
        document.getElementById("sc-self-closing").checked = !!sc.is_self_closing;
        document.getElementById("sc-template").value = sc.html_template || "";
        document.getElementById("sc-example").value = sc.example || "";
        document.getElementById("sc-active").checked = sc.is_active !== false;
        dialog.showModal();
    }

    document.getElementById("sc-new").addEventListener("click", openCreate);
    document.getElementById("sc-cancel").addEventListener("click", function () {
        dialog.close();
    });

    tbody.addEventListener("click", function (e) {
        const editBtn = e.target.closest(".js-edit");
        if (editBtn) {
            openEdit(editBtn.getAttribute("data-id"));
            return;
        }
        const delBtn = e.target.closest(".js-del");
        if (!delBtn) return;
        const id = delBtn.getAttribute("data-id");
        if (!window.confirm("حذف شود؟")) return;
        api.setBusy(delBtn, true, "حذف...");
        api.apiFetch("/api/v1/store-admin/cms/shortcodes/" + id, { method: "DELETE" }).then(function (res) {
            if (!res.ok) {
                api.setBusy(delBtn, false);
                api.flash(res.data?.detail || "حذف ناموفق", true);
                return;
            }
            api.flash("حذف شد");
            load();
        });
    });

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const id = document.getElementById("sc-id").value;
        const saveBtn = form.querySelector('button[type="submit"]');
        const payload = {
            name: document.getElementById("sc-name").value.trim(),
            label: document.getElementById("sc-label").value.trim(),
            description: document.getElementById("sc-description").value.trim(),
            html_template: document.getElementById("sc-template").value,
            is_self_closing: document.getElementById("sc-self-closing").checked,
            example: document.getElementById("sc-example").value,
            is_active: document.getElementById("sc-active").checked,
        };
        const path = id
            ? "/api/v1/store-admin/cms/shortcodes/" + id
            : "/api/v1/store-admin/cms/shortcodes";
        const method = id ? "PUT" : "POST";
        api.setBusy(saveBtn, true, "در حال ذخیره...");
        api.apiFetch(path, { method: method, body: JSON.stringify(payload) }).then(function (res) {
            api.setBusy(saveBtn, false);
            if (!res.ok) {
                api.flash(res.data?.detail || "ذخیره ناموفق", true);
                return;
            }
            api.flash("ذخیره شد");
            dialog.close();
            load();
        });
    });

    load();
})();
