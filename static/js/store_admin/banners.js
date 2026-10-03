(function () {
    const api = window.StoreAdminApi;
    if (!api || !api.requireAuth("/manage/banners/")) return;

    const POSITIONS = {
        home_top: "بالای صفحه خانه",
        home_middle: "وسط صفحه خانه",
        category_top: "بالای دسته‌بندی",
        sidebar: "سایدبار",
    };

    const tbody = document.getElementById("bn-tbody");
    const host = document.getElementById("bn-table-host");
    const dialog = document.getElementById("bn-dialog");
    const picker = document.getElementById("bn-picker");
    const pickerGrid = document.getElementById("bn-picker-grid");
    const form = document.getElementById("bn-form");
    const imageInput = document.getElementById("bn-image");
    const preview = document.getElementById("bn-preview");
    const previewImg = document.getElementById("bn-preview-img");
    let items = [];

    function escapeHtml(s) {
        return api.escapeHtml(s);
    }

    function toLocalInput(iso) {
        if (!iso) return "";
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return "";
        const pad = function (n) {
            return String(n).padStart(2, "0");
        };
        return (
            d.getFullYear() +
            "-" +
            pad(d.getMonth() + 1) +
            "-" +
            pad(d.getDate()) +
            "T" +
            pad(d.getHours()) +
            ":" +
            pad(d.getMinutes())
        );
    }

    function optionalDate(id) {
        const raw = (document.getElementById(id).value || "").trim();
        return raw || null;
    }

    function syncPreview() {
        const url = (imageInput.value || "").trim();
        if (!url) {
            preview.hidden = true;
            previewImg.removeAttribute("src");
            return;
        }
        previewImg.src = url;
        preview.hidden = false;
    }

    function thumbUrl(file) {
        if (!file) return "";
        const thumbs = file.thumbnails || [];
        const prefer = thumbs.find(function (t) {
            return t.variant === "small" || t.variant === "thumb";
        });
        return (prefer && prefer.url) || file.url || "";
    }

    function render() {
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="sa-muted">بنری ثبت نشده</td></tr>';
            return;
        }
        tbody.innerHTML = items
            .map(function (bn) {
                const status = bn.is_active
                    ? '<span class="sa-badge sa-badge-ok">فعال</span>'
                    : '<span class="sa-badge sa-badge-muted">غیرفعال</span>';
                return (
                    "<tr>" +
                    "<td>" +
                    escapeHtml(bn.title) +
                    "</td>" +
                    "<td>" +
                    escapeHtml(POSITIONS[bn.position] || bn.position) +
                    "</td>" +
                    "<td>" +
                    escapeHtml(bn.sort_order) +
                    "</td>" +
                    "<td>" +
                    status +
                    "</td>" +
                    '<td class="sa-row-actions">' +
                    '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm js-edit" data-id="' +
                    bn.id +
                    '">ویرایش</button> ' +
                    '<button type="button" class="sa-btn sa-btn-danger sa-btn-sm js-del" data-id="' +
                    bn.id +
                    '">حذف</button>' +
                    "</td></tr>"
                );
            })
            .join("");
    }

    function load() {
        api.setPageLoading(host, true);
        api.apiFetch("/api/v1/store-admin/cms/banners").then(function (res) {
            api.setPageLoading(host, false);
            if (!res.ok) {
                tbody.innerHTML = '<tr><td colspan="5" class="sa-muted">خطا در دریافت بنرها</td></tr>';
                return;
            }
            items = Array.isArray(res.data) ? res.data : [];
            render();
        });
    }

    function fillForm(bn) {
        document.getElementById("bn-id").value = bn ? bn.id : "";
        document.getElementById("bn-dialog-title").textContent = bn ? "ویرایش بنر" : "بنر جدید";
        document.getElementById("bn-title").value = bn ? bn.title || "" : "";
        document.getElementById("bn-subtitle").value = bn ? bn.subtitle || "" : "";
        document.getElementById("bn-position").value = bn && bn.position ? bn.position : "home_top";
        imageInput.value = bn ? bn.image || "" : "";
        document.getElementById("bn-link").value = bn ? bn.link || "" : "";
        document.getElementById("bn-sort").value = bn && bn.sort_order != null ? bn.sort_order : 0;
        document.getElementById("bn-starts").value = bn ? toLocalInput(bn.starts_at) : "";
        document.getElementById("bn-ends").value = bn ? toLocalInput(bn.ends_at) : "";
        document.getElementById("bn-active").checked = bn ? bn.is_active !== false : true;
        syncPreview();
    }

    function openDialog(bn) {
        fillForm(bn || null);
        dialog.showModal();
    }

    function closePicker() {
        if (typeof picker.close === "function") picker.close();
        else picker.removeAttribute("open");
    }

    function loadPicker() {
        pickerGrid.innerHTML = api.loadingHtml(null, { compact: true });
        api.apiFetch("/api/v1/store-admin/files?file_type=image&page=1").then(function (res) {
            if (!res.ok) {
                pickerGrid.innerHTML =
                    '<div class="sa-empty">' +
                    escapeHtml((res.data && res.data.detail) || "خطا در دریافت رسانه") +
                    "</div>";
                return;
            }
            const files = api.unwrapList(res.data);
            if (!files.length) {
                pickerGrid.innerHTML =
                    '<div class="sa-empty">تصویری نیست. از بخش رسانه آپلود کنید.</div>';
                return;
            }
            pickerGrid.innerHTML = files
                .map(function (file) {
                    const url = file.url || "";
                    return (
                        '<button type="button" class="sa-picker-item" data-url="' +
                        escapeHtml(url) +
                        '">' +
                        '<img src="' +
                        escapeHtml(thumbUrl(file) || url) +
                        '" alt="">' +
                        "<span>" +
                        escapeHtml(file.title || file.original_name || "تصویر") +
                        "</span></button>"
                    );
                })
                .join("");
        });
    }

    document.getElementById("bn-new").addEventListener("click", function () {
        openDialog(null);
    });
    document.getElementById("bn-cancel").addEventListener("click", function () {
        dialog.close();
    });
    imageInput.addEventListener("input", syncPreview);

    document.getElementById("bn-pick").addEventListener("click", function () {
        if (typeof picker.showModal === "function") picker.showModal();
        else picker.setAttribute("open", "");
        loadPicker();
    });
    document.getElementById("bn-picker-close").addEventListener("click", closePicker);
    pickerGrid.addEventListener("click", function (e) {
        const btn = e.target.closest(".sa-picker-item");
        if (!btn) return;
        imageInput.value = btn.getAttribute("data-url") || "";
        syncPreview();
        closePicker();
    });

    tbody.addEventListener("click", function (e) {
        const editBtn = e.target.closest(".js-edit");
        if (editBtn) {
            const bn = items.find(function (x) {
                return String(x.id) === String(editBtn.getAttribute("data-id"));
            });
            if (bn) openDialog(bn);
            return;
        }
        const delBtn = e.target.closest(".js-del");
        if (!delBtn) return;
        const id = delBtn.getAttribute("data-id");
        if (!window.confirm("این بنر حذف شود؟")) return;
        api.setBusy(delBtn, true, "حذف...");
        api.apiFetch("/api/v1/store-admin/cms/banners/" + id, { method: "DELETE" }).then(function (res) {
            if (!res.ok) {
                api.setBusy(delBtn, false);
                api.flash((res.data && res.data.detail) || "حذف ناموفق", true);
                return;
            }
            api.flash("بنر حذف شد");
            load();
        });
    });

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const id = document.getElementById("bn-id").value;
        const saveBtn = form.querySelector('button[type="submit"]');
        const payload = {
            title: document.getElementById("bn-title").value.trim(),
            subtitle: document.getElementById("bn-subtitle").value.trim(),
            position: document.getElementById("bn-position").value,
            image: imageInput.value.trim(),
            link: document.getElementById("bn-link").value.trim(),
            sort_order: Number(document.getElementById("bn-sort").value || 0),
            is_active: document.getElementById("bn-active").checked,
            starts_at: optionalDate("bn-starts"),
            ends_at: optionalDate("bn-ends"),
        };
        const path = id
            ? "/api/v1/store-admin/cms/banners/" + id
            : "/api/v1/store-admin/cms/banners";
        api.setBusy(saveBtn, true, "ذخیره...");
        api.apiFetch(path, {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(payload),
        }).then(function (res) {
            api.setBusy(saveBtn, false);
            if (!res.ok) {
                api.flash((res.data && res.data.detail) || "ذخیره انجام نشد", true);
                return;
            }
            dialog.close();
            api.flash(id ? "بنر ویرایش شد" : "بنر ساخته شد");
            load();
        });
    });

    load();
})();
