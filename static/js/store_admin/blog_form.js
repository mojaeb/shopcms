(function () {
    const api = window.StoreAdminApi;
    const rte = window.StoreAdminRichText;
    if (!api || !api.requireAuth() || !rte) return;

    const root = document.getElementById("sa-blog-form");
    const form = document.getElementById("blog-form");
    const stickyBar = document.getElementById("blog-sticky-bar");
    const saveBtn = document.getElementById("blog-save");
    const isEdit = root.dataset.isEdit === "1";
    const postId = root.dataset.postId;
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

    document.getElementById("blog-title").addEventListener("input", function () {
        if (slugTouched) return;
        document.getElementById("blog-slug").value = slugify(this.value);
    });
    document.getElementById("blog-slug").addEventListener("input", function () {
        slugTouched = true;
    });

    function fillCategories(categories, selectedId) {
        const sel = document.getElementById("blog-category");
        sel.innerHTML = '<option value="">— بدون دسته —</option>' +
            (categories || []).map(function (c) {
                return '<option value="' + c.id + '">' + api.escapeHtml(c.name) + "</option>";
            }).join("");
        if (selectedId) sel.value = String(selectedId);
    }

    form.hidden = false;
    stickyBar.hidden = false;
    api.setPageLoading(root, true);

    Promise.all([
        api.apiFetch("/api/v1/store-admin/blog/categories"),
        rte.loadShortcodes(api),
    ]).then(function (results) {
        const catRes = results[0];
        const shortcodes = results[1] || [];
        if (catRes.ok) fillCategories(Array.isArray(catRes.data) ? catRes.data : []);
        return rte.init("#blog-content", { shortcodes: shortcodes, height: 460 }).then(function () {
            if (!isEdit || !postId) return null;
            return api.apiFetch("/api/v1/store-admin/blog/posts/" + postId);
        });
    }).then(function (res) {
        if (!res) {
            showForm();
            return;
        }
        if (!res.ok) {
            api.setPageLoading(root, false);
            api.flash(res.data?.detail || "مقاله یافت نشد", true);
            return;
        }
        const p = res.data;
        document.getElementById("blog-title").value = p.title || "";
        document.getElementById("blog-slug").value = p.slug || "";
        document.getElementById("blog-excerpt").value = p.excerpt || "";
        document.getElementById("blog-featured").value = p.featured_image || "";
        document.getElementById("blog-published").checked = !!p.is_published;
        document.getElementById("blog-meta-title").value = p.meta_title || "";
        document.getElementById("blog-meta-description").value = p.meta_description || "";
        if (p.category_id) document.getElementById("blog-category").value = String(p.category_id);
        rte.setContent("#blog-content", p.content || "");
        showForm();
    }).catch(function () {
        api.setPageLoading(root, false);
        api.flash("خطا در بارگذاری فرم", true);
    });

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const catVal = document.getElementById("blog-category").value;
        const payload = {
            title: document.getElementById("blog-title").value.trim(),
            slug: document.getElementById("blog-slug").value.trim(),
            excerpt: document.getElementById("blog-excerpt").value.trim(),
            content: rte.getContent("#blog-content"),
            featured_image: document.getElementById("blog-featured").value.trim(),
            category_id: catVal ? parseInt(catVal, 10) : null,
            is_published: document.getElementById("blog-published").checked,
            meta_title: document.getElementById("blog-meta-title").value.trim(),
            meta_description: document.getElementById("blog-meta-description").value.trim(),
        };
        if (!payload.title || !payload.slug) {
            api.flash("عنوان و شناسه الزامی است", true);
            return;
        }
        const path = isEdit
            ? "/api/v1/store-admin/blog/posts/" + postId
            : "/api/v1/store-admin/blog/posts";
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
                window.location.href = "/manage/blog/" + res.data.id + "/edit/";
            }
        });
    });
})();
