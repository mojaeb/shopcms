(function () {
    const root = document.getElementById("sa-files");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/files/")) return;

    const wrap = document.getElementById("files-grid-wrap");
    const pager = document.getElementById("files-pager");
    const pageLabel = document.getElementById("page-label");
    const dialog = document.getElementById("file-dialog");
    const form = document.getElementById("file-form");
    const zone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("file-input");

    let page = 1;
    let hasNext = false;
    let currentFile = null;
    let uploading = false;

    function typeLabel(t) {
        return { image: "تصویر", video: "ویدیو", document: "سند", other: "سایر" }[t] || t || "—";
    }

    function formatBytes(n) {
        const num = Number(n) || 0;
        if (num < 1024) return num + " B";
        if (num < 1024 * 1024) return (num / 1024).toFixed(1) + " KB";
        return (num / (1024 * 1024)).toFixed(2) + " MB";
    }

    function thumbUrl(file) {
        if (!file) return "";
        const thumbs = file.thumbnails || [];
        const prefer = thumbs.find(function (t) {
            return t.variant === "small" || t.variant === "thumb";
        });
        return (prefer && prefer.url) || file.url || "";
    }

    function absoluteUrl(url) {
        if (!url) return "";
        if (/^https?:\/\//i.test(url)) return url;
        return window.location.origin + (url.charAt(0) === "/" ? url : "/" + url);
    }

    function copyText(text) {
        if (!text) return Promise.resolve(false);
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text).then(function () {
                return true;
            });
        }
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try {
            document.execCommand("copy");
            return Promise.resolve(true);
        } catch (e) {
            return Promise.resolve(false);
        } finally {
            document.body.removeChild(ta);
        }
    }

    function queryParams() {
        const params = new URLSearchParams();
        params.set("page", String(page));
        const type = document.getElementById("filter-type").value;
        const folder = document.getElementById("filter-folder").value.trim();
        if (type) params.set("file_type", type);
        if (folder) params.set("folder", folder);
        return params.toString();
    }

    function renderGrid(items) {
        if (!items.length) {
            wrap.innerHTML = '<div class="sa-empty">فایلی یافت نشد. اولین فایل را آپلود کنید.</div>';
            return;
        }
        wrap.innerHTML =
            '<div class="sa-media-grid">' +
            items
                .map(function (f) {
                    const preview =
                        f.file_type === "image"
                            ? '<img src="' +
                              api.escapeHtml(thumbUrl(f)) +
                              '" alt="' +
                              api.escapeHtml(f.alt_text || f.title || f.original_name) +
                              '" loading="lazy">'
                            : '<div class="sa-media-thumb-icon">' +
                              api.escapeHtml(typeLabel(f.file_type)) +
                              "<br>" +
                              api.escapeHtml(f.mime_type || "") +
                              "</div>";
                    const dims =
                        f.width && f.height
                            ? api.formatNumber(f.width) + "×" + api.formatNumber(f.height)
                            : "";
                    return (
                        '<article class="sa-media-card" data-id="' +
                        f.id +
                        '">' +
                        '<div class="sa-media-thumb" data-open="' +
                        f.id +
                        '">' +
                        preview +
                        "</div>" +
                        '<div class="sa-media-body">' +
                        '<div class="sa-media-name" title="' +
                        api.escapeHtml(f.title || f.original_name) +
                        '">' +
                        api.escapeHtml(f.title || f.original_name) +
                        "</div>" +
                        '<div class="sa-media-meta">' +
                        '<span class="sa-badge sa-badge-muted">ID: ' +
                        api.escapeHtml(String(f.id)) +
                        "</span>" +
                        "<span>" +
                        api.escapeHtml(typeLabel(f.file_type)) +
                        "</span>" +
                        "<span>" +
                        api.escapeHtml(formatBytes(f.size_bytes)) +
                        "</span>" +
                        (dims ? "<span>" + dims + "</span>" : "") +
                        (f.folder
                            ? "<span>" + api.escapeHtml(f.folder) + "</span>"
                            : "") +
                        "</div>" +
                        '<div class="sa-media-url" title="' +
                        api.escapeHtml(f.url) +
                        '">' +
                        api.escapeHtml(f.url) +
                        "</div>" +
                        '<div class="sa-media-actions">' +
                        '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm" data-copy-url="' +
                        f.id +
                        '">کپی لینک</button>' +
                        '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm" data-copy-id="' +
                        f.id +
                        '">کپی ID</button>' +
                        '<button type="button" class="sa-btn sa-btn-sm" data-open="' +
                        f.id +
                        '">جزئیات</button>' +
                        "</div></div></article>"
                    );
                })
                .join("") +
            "</div>";

        wrap._items = items;
    }

    function updatePager(data) {
        const count = data && typeof data.count === "number" ? data.count : null;
        hasNext = !!(data && data.next);
        const show = page > 1 || hasNext;
        pager.hidden = !show;
        document.getElementById("page-prev").disabled = page <= 1;
        document.getElementById("page-next").disabled = !hasNext;
        if (count != null) {
            pageLabel.textContent =
                "صفحه " + api.formatNumber(page) + " · " + api.formatNumber(count) + " فایل";
        } else {
            pageLabel.textContent = "صفحه " + api.formatNumber(page);
        }
    }

    function loadFiles() {
        wrap.innerHTML = '<div class="sa-loading">در حال بارگذاری...</div>';
        // Ninja list route is /files (no trailing slash); /files/ returns 404
        api.apiFetch("/api/v1/store-admin/files?" + queryParams()).then(function ({ ok, data }) {
            if (!ok) {
                wrap.innerHTML =
                    '<div class="sa-empty">' +
                    api.escapeHtml((data && data.detail) || "خطا در دریافت فایل‌ها") +
                    "</div>";
                pager.hidden = true;
                return;
            }
            renderGrid(api.unwrapList(data));
            updatePager(data);
        });
    }

    function findItem(id) {
        const items = wrap._items || [];
        return items.find(function (f) {
            return String(f.id) === String(id);
        });
    }

    function openDetail(file) {
        currentFile = file;
        document.getElementById("file-id").value = file.id;
        document.getElementById("detail-id").value = String(file.id);
        document.getElementById("detail-url").value = absoluteUrl(file.url);
        document.getElementById("detail-name").value = file.original_name || "";
        document.getElementById("detail-type").value = typeLabel(file.file_type);
        document.getElementById("detail-size").value = formatBytes(file.size_bytes);
        document.getElementById("detail-dims").value =
            file.width && file.height ? file.width + " × " + file.height : "—";
        document.getElementById("detail-mime").value = file.mime_type || "";
        document.getElementById("detail-title").value = file.title || "";
        document.getElementById("detail-alt").value = file.alt_text || "";
        document.getElementById("detail-folder").value = file.folder || "";

        const preview = document.getElementById("file-preview-wrap");
        if (file.file_type === "image") {
            preview.innerHTML =
                '<img class="sa-detail-preview" src="' +
                api.escapeHtml(file.url) +
                '" alt="">';
        } else {
            preview.innerHTML =
                '<p class="sa-muted">' + api.escapeHtml(typeLabel(file.file_type)) + "</p>";
        }

        const thumbs = file.thumbnails || [];
        const thumbsEl = document.getElementById("detail-thumbs");
        if (thumbs.length) {
            thumbsEl.innerHTML =
                "<strong>نسخه‌های کوچک:</strong><br>" +
                thumbs
                    .map(function (t) {
                        return (
                            api.escapeHtml(t.variant) +
                            ": " +
                            '<a href="' +
                            api.escapeHtml(t.url) +
                            '" target="_blank" rel="noopener">' +
                            api.escapeHtml(t.url) +
                            "</a>"
                        );
                    })
                    .join("<br>");
        } else {
            thumbsEl.innerHTML = "";
        }

        if (typeof dialog.showModal === "function") dialog.showModal();
        else dialog.setAttribute("open", "");
    }

    function uploadFiles(fileList) {
        const files = Array.from(fileList || []);
        if (!files.length || uploading) return;
        uploading = true;
        api.flash("در حال آپلود...");
        const title = document.getElementById("upload-title").value.trim();
        const folder = document.getElementById("upload-folder").value.trim();
        const alt = document.getElementById("upload-alt").value.trim();

        let chain = Promise.resolve();
        let okCount = 0;
        let lastError = "";

        files.forEach(function (file, index) {
            chain = chain.then(function () {
                const fd = new FormData();
                fd.append("file", file);
                fd.append("folder", folder);
                fd.append("title", title || file.name);
                fd.append("alt_text", alt);
                fd.append("is_public", "true");
                api.flash(
                    "آپلود " +
                        api.formatNumber(index + 1) +
                        " از " +
                        api.formatNumber(files.length) +
                        "..."
                );
                return api
                    .apiFetch("/api/v1/store-admin/files/upload", { method: "POST", body: fd })
                    .then(function ({ ok, data }) {
                        if (ok) okCount += 1;
                        else lastError = (data && (data.detail || data.message)) || "خطا در آپلود";
                    });
            });
        });

        chain.finally(function () {
            uploading = false;
            fileInput.value = "";
            page = 1;
            loadFiles();
            if (okCount === files.length) {
                api.flash(api.formatNumber(okCount) + " فایل با موفقیت آپلود شد");
            } else if (okCount) {
                api.flash(
                    api.formatNumber(okCount) +
                        " از " +
                        api.formatNumber(files.length) +
                        " آپلود شد. " +
                        (lastError || ""),
                    true
                );
            } else {
                api.flash(lastError || "آپلود ناموفق بود", true);
            }
        });
    }

    wrap.addEventListener("click", function (e) {
        const openBtn = e.target.closest("[data-open]");
        if (openBtn) {
            const item = findItem(openBtn.getAttribute("data-open"));
            if (item) openDetail(item);
            else {
                api.apiFetch("/api/v1/store-admin/files/" + openBtn.getAttribute("data-open")).then(
                    function ({ ok, data }) {
                        if (ok) openDetail(data);
                        else api.flash((data && data.detail) || "فایل یافت نشد", true);
                    }
                );
            }
            return;
        }
        const copyUrl = e.target.closest("[data-copy-url]");
        if (copyUrl) {
            const item = findItem(copyUrl.getAttribute("data-copy-url"));
            if (!item) return;
            copyText(absoluteUrl(item.url)).then(function (ok) {
                api.flash(ok ? "لینک کپی شد" : "کپی ناموفق", !ok);
            });
            return;
        }
        const copyId = e.target.closest("[data-copy-id]");
        if (copyId) {
            copyText(copyId.getAttribute("data-copy-id")).then(function (ok) {
                api.flash(ok ? "شناسه کپی شد" : "کپی ناموفق", !ok);
            });
        }
    });

    form.addEventListener("click", function (e) {
        const btn = e.target.closest("[data-copy]");
        if (!btn) return;
        e.preventDefault();
        const input = document.getElementById(btn.getAttribute("data-copy"));
        copyText(input && input.value).then(function (ok) {
            api.flash(ok ? "کپی شد" : "کپی ناموفق", !ok);
        });
    });

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const id = document.getElementById("file-id").value;
        if (!id) return;
        const payload = {
            title: document.getElementById("detail-title").value.trim(),
            alt_text: document.getElementById("detail-alt").value.trim(),
            folder: document.getElementById("detail-folder").value.trim(),
        };
        api.apiFetch("/api/v1/store-admin/files/" + id, {
            method: "PUT",
            body: JSON.stringify(payload),
        }).then(function ({ ok, data }) {
            if (!ok) {
                api.flash((data && data.detail) || "ذخیره ناموفق", true);
                return;
            }
            api.flash("ذخیره شد");
            currentFile = data;
            loadFiles();
        });
    });

    document.getElementById("file-delete").addEventListener("click", function () {
        const id = document.getElementById("file-id").value;
        if (!id || !confirm("این فایل حذف شود؟")) return;
        api.apiFetch("/api/v1/store-admin/files/" + id, { method: "DELETE" }).then(function ({
            ok,
            data,
        }) {
            if (!ok) {
                api.flash((data && data.detail) || "حذف ناموفق", true);
                return;
            }
            api.flash("فایل حذف شد");
            dialog.close();
            loadFiles();
        });
    });

    document.getElementById("file-close").addEventListener("click", function () {
        dialog.close();
    });

    document.getElementById("file-pick").addEventListener("click", function () {
        fileInput.click();
    });
    fileInput.addEventListener("change", function () {
        uploadFiles(fileInput.files);
    });

    ["dragenter", "dragover"].forEach(function (ev) {
        zone.addEventListener(ev, function (e) {
            e.preventDefault();
            zone.classList.add("is-drag");
        });
    });
    ["dragleave", "drop"].forEach(function (ev) {
        zone.addEventListener(ev, function (e) {
            e.preventDefault();
            zone.classList.remove("is-drag");
        });
    });
    zone.addEventListener("drop", function (e) {
        uploadFiles(e.dataTransfer && e.dataTransfer.files);
    });

    document.getElementById("filter-apply").addEventListener("click", function () {
        page = 1;
        loadFiles();
    });
    document.getElementById("filter-folder").addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            page = 1;
            loadFiles();
        }
    });
    document.getElementById("filter-type").addEventListener("change", function () {
        page = 1;
        loadFiles();
    });
    document.getElementById("page-prev").addEventListener("click", function () {
        if (page <= 1) return;
        page -= 1;
        loadFiles();
    });
    document.getElementById("page-next").addEventListener("click", function () {
        if (!hasNext) return;
        page += 1;
        loadFiles();
    });

    loadFiles();
})();
