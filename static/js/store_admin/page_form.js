(function () {
    const api = window.StoreAdminApi;
    const rte = window.StoreAdminRichText;
    if (!api || !api.requireAuth() || !rte) return;

    const root = document.getElementById("sa-page-form");
    const form = document.getElementById("page-form");
    const stickyBar = document.getElementById("page-sticky-bar");
    const saveBtn = document.getElementById("page-save");
    const isEdit = root.dataset.isEdit === "1";
    const pageId = root.dataset.pageId;
    let slugTouched = isEdit;

    function slugify(text) {
        return String(text || "")
            .trim()
            .toLowerCase()
            .replace(/\s+/g, "-")
            .replace(/[^a-z0-9\u0600-\u06FF\-]+/g, "")
            .replace(/-+/g, "-");
    }

    function showForm() {
        form.hidden = false;
        stickyBar.hidden = false;
        api.setPageLoading(root, false);
    }

    document.getElementById("page-title").addEventListener("input", function () {
        if (slugTouched) return;
        document.getElementById("page-slug").value = slugify(this.value);
    });
    document.getElementById("page-slug").addEventListener("input", function () {
        slugTouched = true;
    });

    form.hidden = false;
    stickyBar.hidden = false;
    api.setPageLoading(root, true);

    rte.loadShortcodes(api).then(function (shortcodes) {
        return rte.init("#page-content", { shortcodes: shortcodes, height: 420 });
    }).then(function () {
        if (!isEdit || !pageId) {
            showForm();
            return null;
        }
        return api.apiFetch("/api/v1/store-admin/cms/pages/" + pageId).then(function (res) {
            if (!res.ok) {
                api.setPageLoading(root, false);
                api.flash(res.data?.detail || "صفحه یافت نشد", true);
                return;
            }
            const p = res.data;
            document.getElementById("page-title").value = p.title || "";
            document.getElementById("page-slug").value = p.slug || "";
            document.getElementById("page-published").checked = !!p.is_published;
            document.getElementById("page-meta-title").value = p.meta_title || "";
            document.getElementById("page-meta-description").value = p.meta_description || "";
            rte.setContent("#page-content", p.content || "");
            const preview = document.getElementById("page-preview");
            if (preview && p.slug) preview.href = "/page/" + encodeURIComponent(p.slug) + "/";
            showForm();
        });
    }).catch(function () {
        api.setPageLoading(root, false);
        api.flash("خطا در بارگذاری فرم", true);
    });

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const payload = {
            title: document.getElementById("page-title").value.trim(),
            slug: document.getElementById("page-slug").value.trim(),
            content: rte.getContent("#page-content"),
            is_published: document.getElementById("page-published").checked,
            meta_title: document.getElementById("page-meta-title").value.trim(),
            meta_description: document.getElementById("page-meta-description").value.trim(),
        };
        if (!payload.title || !payload.slug) {
            api.flash("عنوان و شناسه الزامی است", true);
            return;
        }
        const path = isEdit
            ? "/api/v1/store-admin/cms/pages/" + pageId
            : "/api/v1/store-admin/cms/pages";
        const method = isEdit ? "PUT" : "POST";
        api.setBusy(saveBtn, true, "در حال ذخیره...");
        api.setPageLoading(root, true, "در حال ذخیره...");
        api.apiFetch(path, { method: method, body: JSON.stringify(payload) }).then(function (res) {
            api.setBusy(saveBtn, false);
            api.setPageLoading(root, false);
            if (!res.ok) {
                api.flash(res.data?.detail || "ذخیره ناموفق", true);
                return;
            }
            api.flash("ذخیره شد");
            if (!isEdit && res.data?.id) {
                window.location.href = "/manage/pages/" + res.data.id + "/edit/";
            }
        });
    });
})();
