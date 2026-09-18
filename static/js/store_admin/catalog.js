(function () {
    const root = document.getElementById("sa-catalog");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/catalog/")) return;

    const catList = document.getElementById("categories-list");
    const brandList = document.getElementById("brands-list");
    const catForm = document.getElementById("category-create-form");
    const brandForm = document.getElementById("brand-create-form");

    function slugify(text) {
        return String(text || "")
            .trim()
            .toLowerCase()
            .replace(/\s+/g, "-")
            .replace(/[^a-z0-9\-]+/g, "")
            .replace(/-+/g, "-")
            .replace(/^-|-$/g, "");
    }

    function bindAutoSlug(nameId, slugId) {
        const nameEl = document.getElementById(nameId);
        const slugEl = document.getElementById(slugId);
        if (!nameEl || !slugEl) return;
        nameEl.addEventListener("input", function () {
            if (slugEl.dataset.touched) return;
            slugEl.value = slugify(nameEl.value);
        });
        slugEl.addEventListener("input", function () {
            slugEl.dataset.touched = "1";
        });
    }

    function rowHtml(item, kind) {
        const count = Number(item.product_count || 0);
        const extra =
            kind === "category" && item.is_custom
                ? ' <span class="sa-badge sa-badge-ok">سفارشی</span>'
                : "";
        const toggle =
            kind === "category"
                ? '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm js-toggle-custom" data-id="' +
                  item.id +
                  '" data-custom="' +
                  (item.is_custom ? "1" : "0") +
                  '">' +
                  (item.is_custom ? "حذف پرچم سفارشی" : "علامت سفارشی") +
                  "</button>"
                : "";
        return (
            '<div class="sa-catalog-row" data-id="' +
            item.id +
            '">' +
            '<div class="sa-catalog-row-main">' +
            "<strong>" +
            api.escapeHtml(item.name) +
            "</strong>" +
            extra +
            '<span class="sa-muted" dir="ltr">' +
            api.escapeHtml(item.slug) +
            "</span>" +
            '<span class="sa-muted">' +
            api.formatNumber(count) +
            " محصول</span>" +
            "</div>" +
            '<div class="sa-catalog-row-actions">' +
            toggle +
            '<button type="button" class="sa-btn sa-btn-danger sa-btn-sm js-delete" data-id="' +
            item.id +
            '" data-name="' +
            api.escapeHtml(item.name) +
            '" data-count="' +
            count +
            '">حذف</button>' +
            "</div></div>"
        );
    }

    function renderList(el, items, kind, emptyText) {
        if (!el) return;
        if (!items.length) {
            el.innerHTML = '<p class="sa-muted">' + emptyText + "</p>";
            return;
        }
        el.innerHTML = items.map(function (item) {
            return rowHtml(item, kind);
        }).join("");
    }

    function loadCategories() {
        return api.apiFetch("/api/v1/store-admin/products/categories/list").then(function ({ ok, data }) {
            if (!ok) {
                api.flash(api.errorDetail(data, "خطا در دریافت دسته‌ها"), true);
                return;
            }
            renderList(catList, api.unwrapList(data), "category", "هنوز دسته‌ای ثبت نشده.");
        });
    }

    function loadBrands() {
        return api.apiFetch("/api/v1/store-admin/products/brands/list").then(function ({ ok, data }) {
            if (!ok) {
                api.flash(api.errorDetail(data, "خطا در دریافت برندها"), true);
                return;
            }
            renderList(brandList, api.unwrapList(data), "brand", "هنوز برندی ثبت نشده.");
        });
    }

    function submitCreate(form, path, payload, successText, reload) {
        const btn = form.querySelector('button[type="submit"]');
        api.setBusy(btn, true, "در حال ذخیره...");
        api.apiFetch(path, { method: "POST", body: JSON.stringify(payload) }).then(function ({ ok, data }) {
            api.setBusy(btn, false);
            if (!ok) {
                api.flash(api.errorDetail(data, "ثبت ناموفق"), true);
                return;
            }
            api.flash(successText);
            form.reset();
            const slugEl = form.querySelector('[id$="-slug"]');
            if (slugEl) slugEl.dataset.touched = "";
            reload();
        });
    }

    bindAutoSlug("cat-name", "cat-slug");
    bindAutoSlug("brand-name", "brand-slug");

    if (catForm) {
        catForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const name = document.getElementById("cat-name").value.trim();
            if (!name) {
                api.flash("نام دسته الزامی است", true);
                return;
            }
            submitCreate(
                catForm,
                "/api/v1/store-admin/products/categories",
                {
                    name: name,
                    slug: document.getElementById("cat-slug").value.trim(),
                    image: document.getElementById("cat-image").value.trim(),
                    is_custom: document.getElementById("cat-is-custom").checked,
                },
                "دسته ایجاد شد",
                loadCategories
            );
        });
    }

    if (brandForm) {
        brandForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const name = document.getElementById("brand-name").value.trim();
            if (!name) {
                api.flash("نام برند الزامی است", true);
                return;
            }
            submitCreate(
                brandForm,
                "/api/v1/store-admin/products/brands",
                {
                    name: name,
                    slug: document.getElementById("brand-slug").value.trim(),
                    logo: document.getElementById("brand-logo").value.trim(),
                },
                "برند ایجاد شد",
                loadBrands
            );
        });
    }

    if (catList) {
        catList.addEventListener("click", function (e) {
            const toggle = e.target.closest(".js-toggle-custom");
            if (toggle) {
                const id = toggle.getAttribute("data-id");
                const next = toggle.getAttribute("data-custom") !== "1";
                api.apiFetch("/api/v1/store-admin/products/categories/" + id, {
                    method: "PATCH",
                    body: JSON.stringify({ is_custom: next }),
                }).then(function ({ ok, data }) {
                    if (!ok) {
                        api.flash(api.errorDetail(data, "به‌روزرسانی ناموفق"), true);
                        return;
                    }
                    api.flash(next ? "دسته سفارشی شد" : "پرچم سفارشی برداشته شد");
                    loadCategories();
                });
                return;
            }
            const del = e.target.closest(".js-delete");
            if (!del) return;
            const name = del.getAttribute("data-name") || "این دسته";
            const count = Number(del.getAttribute("data-count") || 0);
            const warn = count
                ? " «" + name + "» حذف شود؟ " + api.formatNumber(count) + " محصول بدون دسته می‌مانند."
                : "دسته «" + name + "» حذف شود؟";
            if (!window.confirm(warn)) return;
            api.apiFetch("/api/v1/store-admin/products/categories/" + del.getAttribute("data-id"), {
                method: "DELETE",
            }).then(function ({ ok, data }) {
                if (!ok) {
                    api.flash(api.errorDetail(data, "حذف ناموفق"), true);
                    return;
                }
                api.flash("دسته حذف شد");
                loadCategories();
            });
        });
    }

    if (brandList) {
        brandList.addEventListener("click", function (e) {
            const del = e.target.closest(".js-delete");
            if (!del) return;
            const name = del.getAttribute("data-name") || "این برند";
            const count = Number(del.getAttribute("data-count") || 0);
            const warn = count
                ? "برند «" + name + "» حذف شود؟ " + api.formatNumber(count) + " محصول بدون برند می‌مانند."
                : "برند «" + name + "» حذف شود؟";
            if (!window.confirm(warn)) return;
            api.apiFetch("/api/v1/store-admin/products/brands/" + del.getAttribute("data-id"), {
                method: "DELETE",
            }).then(function ({ ok, data }) {
                if (!ok) {
                    api.flash(api.errorDetail(data, "حذف ناموفق"), true);
                    return;
                }
                api.flash("برند حذف شد");
                loadBrands();
            });
        });
    }

    api.setPageLoading(root, true);
    Promise.all([loadCategories(), loadBrands()]).then(function () {
        api.setPageLoading(root, false);
    });
})();
