(function () {
    const root = document.getElementById("sa-product-form");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    const rte = window.StoreAdminRichText;

    const productIdAttr = root.getAttribute("data-product-id") || "";
    const isEdit = root.getAttribute("data-is-edit") === "1";
    const authPath = isEdit
        ? "/manage/products/" + productIdAttr + "/edit/"
        : "/manage/products/new/";
    if (!api.requireAuth(authPath)) return;

    const form = document.getElementById("product-form");
    const stickyBar = document.getElementById("product-sticky-bar");
    const imagesEl = document.getElementById("product-images");
    const imagesEmpty = document.getElementById("product-images-empty");
    const variantsEl = document.getElementById("product-variants");
    const imageTpl = document.getElementById("product-image-template");
    const variantTpl = document.getElementById("product-variant-template");
    const picker = document.getElementById("media-picker");
    const pickerGrid = document.getElementById("picker-grid");
    const pickerFileInput = document.getElementById("picker-file-input");

    let categories = [];
    let brands = [];
    let attributes = [];
    let pickerTarget = null;
    let pickerMode = "gallery";
    let pickerSelected = [];

    function slugify(text) {
        return String(text || "")
            .trim()
            .toLowerCase()
            .replace(/\s+/g, "-")
            .replace(/[^a-z0-9\-]+/g, "")
            .replace(/-+/g, "-")
            .replace(/^-|-$/g, "");
    }

    function defaultAttrSlug(name) {
        const n = String(name || "").trim();
        if (n === "رنگ" || n.toLowerCase() === "color") return "color";
        return slugify(n) || "attr";
    }

    function parseAttributeValues(raw, displayType) {
        const text = String(raw || "").trim();
        if (!text) return [];
        if (displayType === "color" && (text.includes("\n") || text.includes("|") || text.includes(":"))) {
            return text
                .split(/[|\n]+/)
                .map(function (line) {
                    return line.trim();
                })
                .filter(Boolean)
                .map(function (line, idx) {
                    const colon = line.indexOf(":");
                    let label = line;
                    let colorCode = "";
                    if (colon > 0) {
                        label = line.slice(0, colon).trim();
                        colorCode = line
                            .slice(colon + 1)
                            .trim()
                            .replace(/\s+/g, "");
                    }
                    return {
                        value: label,
                        slug: slugify(label) || "c-" + idx,
                        color_code: colorCode,
                    };
                });
        }
        return text
            .split(/[,،]/)
            .map(function (v) {
                return v.trim();
            })
            .filter(Boolean)
            .map(function (v, idx) {
                return { value: v, slug: slugify(v) || "v-" + idx };
            });
    }

    function colorChipHtml(v) {
        const codes = Array.isArray(v.color_codes) && v.color_codes.length
            ? v.color_codes
            : String(v.color_code || "")
                  .split(/[,،/\s]+/)
                  .map(function (p) {
                      return p.trim();
                  })
                  .filter(Boolean);
        let swatch = "";
        if (codes.length) {
            const bg =
                codes.length === 1
                    ? codes[0]
                    : "conic-gradient(from 135deg, " +
                      codes
                          .map(function (c, i) {
                              const a = ((i / codes.length) * 100).toFixed(2);
                              const b = (((i + 1) / codes.length) * 100).toFixed(2);
                              return c + " " + a + "% " + b + "%";
                          })
                          .join(", ") +
                      ")";
            swatch =
                '<span class="sa-color-dot" style="background:' +
                bg +
                '" title="' +
                api.escapeHtml(codes.join(", ")) +
                '"></span>';
        }
        return '<span class="sa-chip-val">' + swatch + api.escapeHtml(v.value) + "</span>";
    }

    function statusLabel(status) {
        return { draft: "پیش‌نویس", active: "فعال", inactive: "غیرفعال" }[status] || status || "—";
    }

    function statusBadgeClass(status) {
        return status === "active" ? "sa-badge-ok" : status === "draft" ? "sa-badge-warn" : "sa-badge-muted";
    }

    function updateStickyMeta() {
        const name = document.getElementById("product-name").value.trim();
        const status = document.getElementById("product-status").value;
        const titleEl = document.getElementById("sticky-title");
        const statusEl = document.getElementById("sticky-status");
        titleEl.textContent = name || (isEdit ? "ویرایش محصول" : "محصول جدید");
        statusEl.textContent = statusLabel(status);
        statusEl.className = "sa-badge " + statusBadgeClass(status);
    }

    function fillSelect(selectId, items, selectedId, emptyLabel) {
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">' + emptyLabel + "</option>";
        items.forEach(function (item) {
            const opt = document.createElement("option");
            opt.value = item.id;
            opt.textContent = item.name;
            if (selectedId && String(selectedId) === String(item.id)) opt.selected = true;
            select.appendChild(opt);
        });
    }

    const catalogQuick = document.getElementById("catalog-quick-dialog");
    const catalogQuickForm = document.getElementById("catalog-quick-form");
    const catalogQuickName = document.getElementById("catalog-quick-name");
    const catalogQuickSlug = document.getElementById("catalog-quick-slug");
    let catalogQuickKind = "category";

    function openCatalogQuick(kind) {
        catalogQuickKind = kind === "brand" ? "brand" : "category";
        document.getElementById("catalog-quick-title").textContent =
            catalogQuickKind === "brand" ? "برند جدید" : "دسته جدید";
        catalogQuickName.value = "";
        catalogQuickSlug.value = "";
        catalogQuickSlug.dataset.touched = "";
        if (typeof catalogQuick.showModal === "function") catalogQuick.showModal();
        else catalogQuick.setAttribute("open", "");
        catalogQuickName.focus();
    }

    function closeCatalogQuick() {
        if (!catalogQuick) return;
        if (typeof catalogQuick.close === "function") catalogQuick.close();
        else catalogQuick.removeAttribute("open");
    }

    function isVariable() {
        return document.getElementById("product-type").value === "variable";
    }

    function syncTypeUI() {
        const variable = isVariable();
        document.getElementById("product-stock-wrap").hidden = variable;
        document.getElementById("product-variants-section").hidden = !variable;
        const typeHint = document.getElementById("product-type-hint");
        if (typeHint) typeHint.hidden = !variable;
        if (variable) {
            renderAttributesSummary();
            refreshVariantAttrSelects();
            syncVariantsEmpty();
        }
    }

    function hasAttrValues() {
        return attributes.some(function (a) {
            return (a.values || []).length > 0;
        });
    }

    function syncGenerateBtn() {
        const btn = document.getElementById("product-generate-variants");
        if (!btn) return;
        const ready = hasAttrValues();
        btn.disabled = !ready;
        btn.title = ready ? "همه ترکیب‌های ممکن از ویژگی‌ها ساخته می‌شود" : "ابتدا یک ویژگی با مقدار بسازید";
    }

    function syncVariantsEmpty() {
        const empty = document.getElementById("product-variants-empty");
        const head = document.getElementById("product-variants-head");
        const countEl = document.getElementById("variant-count");
        const n = variantsEl.children.length;
        if (empty) {
            empty.hidden = n > 0;
            if (!attributes.length) {
                empty.innerHTML =
                    "<strong>اول ویژگی بسازید</strong><span>رنگ یا سایز را در مرحله ۱ تعریف کنید، بعد ترکیب‌ها ساخته می‌شوند.</span>";
            } else if (!n) {
                empty.innerHTML =
                    "<strong>ترکیبی نیست</strong><span>با «ساخت همه ترکیب‌ها» همه حالت‌ها را یکجا بسازید، یا یکی اضافه کنید.</span>";
            }
        }
        if (head) head.hidden = n === 0;
        if (countEl) countEl.textContent = api.formatNumber(n) + " ترکیب";
        syncGenerateBtn();
        markDuplicateVariants();
    }

    function variantComboKey(row) {
        return Array.from(row.querySelectorAll(".js-variant-attrs select"))
            .map(function (el) {
                return el.value || "";
            })
            .join("|");
    }

    function markDuplicateVariants() {
        const rows = Array.from(variantsEl.querySelectorAll(".sa-variant-row"));
        const counts = {};
        rows.forEach(function (row) {
            const key = variantComboKey(row);
            counts[key] = (counts[key] || 0) + 1;
        });
        rows.forEach(function (row) {
            const key = variantComboKey(row);
            const incomplete = !key || key.split("|").some(function (part) {
                return !part;
            });
            const dup = !incomplete && counts[key] > 1;
            row.classList.toggle("is-duplicate", dup);
            const msg = row.querySelector(".js-variant-dup");
            if (msg) msg.hidden = !dup;
        });
    }

    function cartesian(sets) {
        return sets.reduce(
            function (acc, set) {
                const out = [];
                acc.forEach(function (prefix) {
                    set.forEach(function (item) {
                        out.push(prefix.concat([item]));
                    });
                });
                return out;
            },
            [[]]
        );
    }

    function generateAllVariants() {
        const sets = attributes
            .map(function (a) {
                return (a.values || []).map(function (v) {
                    return v.id;
                });
            })
            .filter(function (set) {
                return set.length > 0;
            });
        if (!sets.length) {
            api.flash("ابتدا حداقل یک ویژگی با مقدار بسازید", true);
            return;
        }
        const combos = cartesian(sets);
        if (combos.length > 48) {
            api.flash("تعداد ترکیب‌ها بیش از ۴۸ است. ویژگی‌ها را کمتر کنید یا دستی اضافه کنید.", true);
            return;
        }
        const existing = new Set(
            Array.from(variantsEl.querySelectorAll(".sa-variant-row")).map(variantComboKey)
        );
        let added = 0;
        combos.forEach(function (ids) {
            const key = ids.map(String).join("|");
            if (existing.has(key)) return;
            addVariantRow({ attribute_value_ids: ids });
            existing.add(key);
            added += 1;
        });
        if (!added) api.flash("همه ترکیب‌ها از قبل وجود دارند");
        else api.flash(api.formatNumber(added) + " ترکیب ساخته شد");
    }

    function renumberVariants() {
        variantsEl.querySelectorAll(".sa-variant-row").forEach(function (row) {
            updateVariantSummary(row);
        });
        markDuplicateVariants();
    }

    function updateVariantSummary(row) {
        const summaryEl = row.querySelector(".js-variant-summary");
        if (!summaryEl) return;
        const selects = row.querySelectorAll(".js-variant-attrs select");
        const parts = [];
        selects.forEach(function (sel) {
            const opt = sel.options[sel.selectedIndex];
            if (sel.value && opt) parts.push(opt.textContent);
        });
        summaryEl.textContent = parts.length ? parts.join(" · ") : "انتخاب ویژگی‌ها";
        markDuplicateVariants();
    }

    function syncImagesEmpty() {
        imagesEmpty.hidden = imagesEl.children.length > 0;
    }

    function updateImagePreview(row) {
        const url = row.querySelector('[name="image"]').value.trim();
        const preview = row.querySelector(".sa-image-preview");
        if (!url) {
            preview.innerHTML = '<div class="sa-image-preview-empty">بدون پیش‌نمایش</div>';
            return;
        }
        const img = document.createElement("img");
        img.alt = "";
        img.loading = "lazy";
        img.src = url;
        img.addEventListener("error", function () {
            preview.innerHTML = '<div class="sa-image-preview-empty">پیش‌نمایش نامعتبر</div>';
        });
        preview.innerHTML = "";
        preview.appendChild(img);
    }

    function displayTypeLabel(type, buttonStyle) {
        var labels = { color: "رنگ", list: "لیست", select: "لیست", button: "دکمه" };
        var text = labels[type] || type || "—";
        if (type === "button" && buttonStyle) {
            text +=
                " · " +
                ({ icon: "فقط آیکون", text: "فقط متن", icon_text: "آیکون + متن" }[buttonStyle] || buttonStyle);
        }
        return text;
    }

    function renderAttributesSummary() {
        const el = document.getElementById("attributes-list");
        if (!attributes.length) {
            el.innerHTML =
                '<div class="sa-variant-empty sa-mt-0"><strong>ویژگی ندارید</strong><span>با «ویژگی جدید» رنگ، سایز یا حافظه را بسازید.</span></div>';
            syncGenerateBtn();
            return;
        }
        el.innerHTML = attributes
            .map(function (a) {
                const chips = (a.values || [])
                    .map(function (v) {
                        return a.display_type === "color" ? colorChipHtml(v) : '<span class="sa-chip-val">' + api.escapeHtml(v.value) + "</span>";
                    })
                    .join("");
                return (
                    '<div class="sa-attr-card">' +
                    '<div class="sa-attr-card-top">' +
                    "<strong>" +
                    api.escapeHtml(a.name) +
                    "</strong>" +
                    '<span class="sa-badge sa-badge-muted">' +
                    api.escapeHtml(displayTypeLabel(a.display_type, a.button_style)) +
                    "</span></div>" +
                    '<div class="sa-attr-chips">' +
                    (chips || '<span class="sa-muted">بدون مقدار</span>') +
                    "</div></div>"
                );
            })
            .join("");
        syncGenerateBtn();
    }

    function buildAttrSelects(container, selectedIds) {
        selectedIds = (selectedIds || []).map(String);
        container.innerHTML = "";
        if (!attributes.length) {
            container.innerHTML =
                '<p class="sa-muted sa-variant-step-hint sa-attr-values">ابتدا یک ویژگی در مرحله ۱ بسازید.</p>';
            return;
        }
        attributes.forEach(function (attr) {
            const label = document.createElement("label");
            label.appendChild(document.createTextNode(attr.name));
            const select = document.createElement("select");
            select.className = "sa-input";
            select.dataset.attrId = String(attr.id);
            const empty = document.createElement("option");
            empty.value = "";
            empty.textContent = "انتخاب کنید…";
            select.appendChild(empty);
            (attr.values || []).forEach(function (val) {
                const opt = document.createElement("option");
                opt.value = val.id;
                opt.textContent = val.value;
                if (selectedIds.indexOf(String(val.id)) >= 0) opt.selected = true;
                select.appendChild(opt);
            });
            label.appendChild(select);
            container.appendChild(label);
        });
    }

    function refreshVariantAttrSelects() {
        variantsEl.querySelectorAll(".sa-variant-row").forEach(function (row) {
            const box = row.querySelector(".js-variant-attrs");
            const selected = Array.from(box.querySelectorAll("select"))
                .map(function (el) {
                    return el.value;
                })
                .filter(Boolean);
            buildAttrSelects(box, selected);
            updateVariantSummary(row);
        });
    }

    function addImageRow(data) {
        data = data || {};
        const node = imageTpl.content.cloneNode(true);
        const row = node.querySelector(".sa-image-card");
        const urlInput = row.querySelector('[name="image"]');
        urlInput.value = data.image || "";
        row.querySelector('[name="alt_text"]').value = data.alt_text || "";
        row.querySelector('[name="is_primary"]').checked = !!data.is_primary;
        updateImagePreview(row);
        urlInput.addEventListener("input", function () {
            updateImagePreview(row);
        });
        row.querySelector(".js-remove-image").addEventListener("click", function () {
            row.remove();
            syncImagesEmpty();
        });
        row.querySelector(".js-pick-row").addEventListener("click", function () {
            openPicker("row", row);
        });
        imagesEl.appendChild(row);
        syncImagesEmpty();
        return row;
    }

    function addVariantRow(data) {
        data = data || {};
        const node = variantTpl.content.cloneNode(true);
        const row = node.querySelector(".sa-variant-row");
        row.querySelector('[name="variant_id"]').value = data.id || "";
        row.querySelector('[name="sku"]').value = data.sku || "";
        row.querySelector('[name="price"]').value =
            data.price != null ? data.price : document.getElementById("product-price").value || 0;
        row.querySelector('[name="compare_price"]').value = data.compare_price != null ? data.compare_price : "";
        row.querySelector('[name="stock"]').value = data.stock != null ? data.stock : 0;
        row.querySelector('[name="is_active"]').checked = data.is_active !== false;
        const attrsBox = row.querySelector(".js-variant-attrs");
        buildAttrSelects(attrsBox, data.attribute_value_ids || []);
        attrsBox.addEventListener("change", function () {
            updateVariantSummary(row);
        });
        row.querySelector(".js-remove-variant").addEventListener("click", function () {
            row.remove();
            renumberVariants();
            syncVariantsEmpty();
        });
        variantsEl.appendChild(row);
        renumberVariants();
        syncVariantsEmpty();
    }

    function collectVariants() {
        return Array.from(variantsEl.querySelectorAll(".sa-variant-row")).map(function (row) {
            const idVal = row.querySelector('[name="variant_id"]').value;
            const compare = row.querySelector('[name="compare_price"]').value;
            const attribute_value_ids = Array.from(row.querySelectorAll(".js-variant-attrs select"))
                .map(function (el) {
                    return el.value ? Number(el.value) : null;
                })
                .filter(function (v) {
                    return v != null;
                });
            return {
                id: idVal ? Number(idVal) : null,
                sku: row.querySelector('[name="sku"]').value.trim(),
                price: Number(row.querySelector('[name="price"]').value || 0),
                compare_price: compare === "" ? null : Number(compare),
                stock: Number(row.querySelector('[name="stock"]').value || 0),
                is_active: row.querySelector('[name="is_active"]').checked,
                attribute_value_ids: attribute_value_ids,
            };
        });
    }

    function collectImages() {
        return Array.from(imagesEl.querySelectorAll(".sa-image-card"))
            .map(function (row, idx) {
                return {
                    image: row.querySelector('[name="image"]').value.trim(),
                    alt_text: row.querySelector('[name="alt_text"]').value.trim(),
                    is_primary: row.querySelector('[name="is_primary"]').checked,
                    sort_order: idx,
                };
            })
            .filter(function (img) {
                return !!img.image;
            });
    }

    function collectTags() {
        return document
            .getElementById("product-tags")
            .value.split(/[,،]/)
            .map(function (t) {
                return t.trim();
            })
            .filter(Boolean);
    }

    function resetForm() {
        form.reset();
        document.getElementById("product-id").value = productIdAttr || "";
        document.getElementById("product-slug").dataset.touched = "";
        imagesEl.innerHTML = "";
        variantsEl.innerHTML = "";
        document.getElementById("attr-create-form").hidden = true;
        fillSelect("product-category", categories, null, "— بدون دسته —");
        fillSelect("product-brand", brands, null, "— بدون برند —");
        syncTypeUI();
        syncImagesEmpty();
        updateStickyMeta();
    }

    function fillProduct(product) {
        document.getElementById("product-id").value = product.id;
        document.getElementById("product-name").value = product.name || "";
        document.getElementById("product-slug").value = product.slug || "";
        document.getElementById("product-slug").dataset.touched = "1";
        document.getElementById("product-type").value = product.product_type || "simple";
        document.getElementById("product-status").value = product.status || "draft";
        document.getElementById("product-price").value = product.base_price || 0;
        document.getElementById("product-compare").value = product.compare_price || "";
        document.getElementById("product-sku").value = product.sku || "";
        document.getElementById("product-stock").value =
            product.stock != null ? product.stock : product.available || 0;
        document.getElementById("product-featured").checked = !!product.is_featured;
        document.getElementById("product-short").value = product.short_description || "";
        if (rte) {
            rte.setContent("#product-description", product.description || "");
        } else {
            document.getElementById("product-description").value = product.description || "";
        }
        document.getElementById("product-tags").value = (product.tags || []).join("، ");
        document.getElementById("product-meta-title").value = product.meta_title || "";
        document.getElementById("product-meta-description").value = product.meta_description || "";
        document.getElementById("product-meta-keywords").value = product.meta_keywords || "";
        document.getElementById("product-og-image").value = product.og_image || "";
        fillSelect("product-category", categories, product.category_id, "— بدون دسته —");
        fillSelect("product-brand", brands, product.brand_id, "— بدون برند —");

        imagesEl.innerHTML = "";
        (product.images || []).forEach(addImageRow);
        syncImagesEmpty();
        syncTypeUI();
        variantsEl.innerHTML = "";
        (product.variants || []).forEach(addVariantRow);
        syncVariantsEmpty();
        updateStickyMeta();
    }

    function showForm() {
        form.hidden = false;
        stickyBar.hidden = false;
        api.setPageLoading(root, false);
    }

    function thumbUrl(file) {
        const thumbs = file.thumbnails || [];
        const prefer = thumbs.find(function (t) {
            return t.variant === "thumb" || t.variant === "small";
        });
        return (prefer && prefer.url) || file.url || "";
    }

    function galleryImageUrls() {
        return new Set(
            Array.from(imagesEl.querySelectorAll('[name="image"]'))
                .map(function (el) {
                    return el.value.trim();
                })
                .filter(Boolean)
        );
    }

    function applyPickedUrl(url, alt) {
        if (!url) return false;
        if (pickerMode === "og") {
            document.getElementById("product-og-image").value = url;
            return true;
        }
        if (pickerMode === "row" && pickerTarget) {
            pickerTarget.querySelector('[name="image"]').value = url;
            const altInput = pickerTarget.querySelector('[name="alt_text"]');
            if (alt && !altInput.value) altInput.value = alt;
            updateImagePreview(pickerTarget);
            return true;
        }
        if (galleryImageUrls().has(url)) return false;
        const row = addImageRow({
            image: url,
            alt_text: alt || "",
            is_primary: imagesEl.children.length === 0,
        });
        updateImagePreview(row);
        return true;
    }

    function isGalleryPicker() {
        return pickerMode === "gallery";
    }

    function syncPickerSelection() {
        const selected = new Set(
            pickerSelected.map(function (item) {
                return item.url;
            })
        );
        pickerGrid.querySelectorAll(".sa-picker-item").forEach(function (btn) {
            btn.classList.toggle("is-selected", selected.has(btn.getAttribute("data-url")));
        });
        const confirm = document.getElementById("picker-confirm");
        const footer = document.getElementById("picker-footer");
        if (!confirm || !footer) return;
        footer.hidden = !isGalleryPicker();
        const n = pickerSelected.length;
        confirm.disabled = n === 0;
        confirm.textContent = n
            ? "افزودن " + api.formatNumber(n) + " تصویر"
            : "افزودن تصاویر";
    }

    function openPicker(mode, targetRow) {
        pickerMode = mode || "gallery";
        pickerTarget = targetRow || null;
        pickerSelected = [];
        const hint = document.getElementById("picker-hint");
        if (hint) {
            hint.textContent = isGalleryPicker()
                ? "چند تصویر را انتخاب کنید، سپس افزودن را بزنید."
                : "روی تصویر کلیک کنید تا انتخاب شود.";
        }
        syncPickerSelection();
        if (typeof picker.showModal === "function") picker.showModal();
        else picker.setAttribute("open", "");
        loadPickerFiles();
    }

    function closePicker() {
        if (typeof picker.close === "function") picker.close();
        else picker.removeAttribute("open");
        pickerTarget = null;
        pickerSelected = [];
    }

    function loadPickerFiles() {
        pickerGrid.innerHTML = api.loadingHtml(null, { compact: true });
        api.apiFetch("/api/v1/store-admin/files?file_type=image&page=1").then(function ({ ok, data }) {
            if (!ok) {
                pickerGrid.innerHTML =
                    '<div class="sa-empty">' +
                    api.escapeHtml((data && data.detail) || "خطا در دریافت رسانه") +
                    "</div>";
                return;
            }
            const items = api.unwrapList(data);
            if (!items.length) {
                pickerGrid.innerHTML =
                    '<div class="sa-empty">تصویری نیست. از دکمه آپلود استفاده کنید.</div>';
                return;
            }
            pickerGrid.innerHTML = items
                .map(function (f) {
                    return (
                        '<button type="button" class="sa-picker-item" data-url="' +
                        api.escapeHtml(f.url) +
                        '" data-alt="' +
                        api.escapeHtml(f.alt_text || f.title || "") +
                        '">' +
                        '<img src="' +
                        api.escapeHtml(thumbUrl(f)) +
                        '" alt="" loading="lazy">' +
                        "<span>" +
                        api.escapeHtml(f.title || f.original_name) +
                        "</span></button>"
                    );
                })
                .join("");
            syncPickerSelection();
        });
    }

    function loadMeta() {
        return Promise.all([
            api.apiFetch("/api/v1/store-admin/products/categories/list"),
            api.apiFetch("/api/v1/store-admin/products/brands/list"),
            api.apiFetch("/api/v1/store-admin/products/attributes/list"),
        ]).then(function (results) {
            categories = results[0].ok ? api.unwrapList(results[0].data) : [];
            brands = results[1].ok ? api.unwrapList(results[1].data) : [];
            attributes = results[2].ok ? api.unwrapList(results[2].data) : [];
        });
    }

    function initCreate() {
        resetForm();
        document.getElementById("product-status").value = "draft";
        document.getElementById("product-type").value = "simple";
        syncTypeUI();
        updateStickyMeta();
        showForm();
    }

    function initEdit(id) {
        api.apiFetch("/api/v1/store-admin/products/" + id).then(function ({ ok, data }) {
            if (!ok) {
                api.setPageLoading(root, false);
                api.flash((data && data.detail) || "محصول یافت نشد", true);
                return;
            }
            resetForm();
            fillProduct(data);
            showForm();
        });
    }

    document.getElementById("product-type").addEventListener("change", syncTypeUI);
    document.getElementById("product-status").addEventListener("change", updateStickyMeta);
    document.getElementById("product-name").addEventListener("input", function (e) {
        updateStickyMeta();
        const id = document.getElementById("product-id").value;
        if (id) return;
        const slugEl = document.getElementById("product-slug");
        if (!slugEl.dataset.touched) slugEl.value = slugify(e.target.value) || "product";
    });
    document.getElementById("product-slug").addEventListener("input", function () {
        this.dataset.touched = "1";
    });

    document.getElementById("product-add-image").addEventListener("click", function () {
        addImageRow({ is_primary: imagesEl.children.length === 0 });
    });
    document.getElementById("product-pick-image").addEventListener("click", function () {
        openPicker("gallery");
    });
    document.getElementById("product-pick-og").addEventListener("click", function () {
        openPicker("og");
    });
    document.getElementById("product-add-category").addEventListener("click", function () {
        openCatalogQuick("category");
    });
    document.getElementById("product-add-brand").addEventListener("click", function () {
        openCatalogQuick("brand");
    });
    if (catalogQuickName && catalogQuickSlug) {
        catalogQuickName.addEventListener("input", function () {
            if (!catalogQuickSlug.dataset.touched) {
                catalogQuickSlug.value = slugify(catalogQuickName.value);
            }
        });
        catalogQuickSlug.addEventListener("input", function () {
            catalogQuickSlug.dataset.touched = "1";
        });
    }
    if (document.getElementById("catalog-quick-cancel")) {
        document.getElementById("catalog-quick-cancel").addEventListener("click", closeCatalogQuick);
    }
    if (catalogQuickForm) {
        catalogQuickForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const name = catalogQuickName.value.trim();
            if (!name) {
                api.flash("نام الزامی است", true);
                return;
            }
            const isBrand = catalogQuickKind === "brand";
            const path = isBrand
                ? "/api/v1/store-admin/products/brands"
                : "/api/v1/store-admin/products/categories";
            const payload = {
                name: name,
                slug: catalogQuickSlug.value.trim(),
            };
            const saveBtn = document.getElementById("catalog-quick-save");
            api.setBusy(saveBtn, true, "در حال ثبت...");
            api.apiFetch(path, { method: "POST", body: JSON.stringify(payload) }).then(function ({ ok, data }) {
                api.setBusy(saveBtn, false);
                if (!ok) {
                    api.flash(api.errorDetail(data, "ثبت ناموفق"), true);
                    return;
                }
                if (isBrand) {
                    brands.push(data);
                    fillSelect("product-brand", brands, data.id, "— بدون برند —");
                    api.flash("برند اضافه شد");
                } else {
                    categories.push(data);
                    fillSelect("product-category", categories, data.id, "— بدون دسته —");
                    api.flash("دسته اضافه شد");
                }
                closeCatalogQuick();
            });
        });
    }
    document.getElementById("product-add-variant").addEventListener("click", function () {
        if (!attributes.length) {
            api.flash("ابتدا حداقل یک ویژگی بسازید", true);
            return;
        }
        addVariantRow({});
    });
    const generateBtn = document.getElementById("product-generate-variants");
    if (generateBtn) {
        generateBtn.addEventListener("click", generateAllVariants);
    }

    document.getElementById("attr-toggle-form").addEventListener("click", function () {
        const box = document.getElementById("attr-create-form");
        box.hidden = !box.hidden;
    });
    document.getElementById("attr-cancel").addEventListener("click", function () {
        document.getElementById("attr-create-form").hidden = true;
    });
    document.getElementById("attr-name").addEventListener("input", function (e) {
        const slugEl = document.getElementById("attr-slug");
        if (!slugEl.dataset.touched) slugEl.value = defaultAttrSlug(e.target.value);
    });
    document.getElementById("attr-slug").addEventListener("input", function () {
        this.dataset.touched = "1";
    });
    document.getElementById("attr-display").addEventListener("change", function () {
        document.getElementById("attr-button-style-wrap").classList.toggle("sa-hidden", this.value !== "button");
        const hint = document.getElementById("attr-values-hint");
        const valuesEl = document.getElementById("attr-values");
        if (this.value === "color") {
            valuesEl.placeholder = "مشکی:#111111,#2a2a2a\nسفید:#f5f5f5\nآبی:#3b82f6,#60a5fa";
            hint.textContent =
                "هر خط یک رنگ: نام یا نام:#hex — برای چندرنگ داخل یک گزینه چند hex با ویرگول بنویسید.";
        } else {
            valuesEl.placeholder = "قرمز، آبی، سبز";
            hint.textContent = "با ویرگول جدا کنید.";
        }
    });
    document.getElementById("attr-save").addEventListener("click", function () {
        const name = document.getElementById("attr-name").value.trim();
        if (!name) {
            api.flash("نام ویژگی الزامی است", true);
            return;
        }
        const displayType = document.getElementById("attr-display").value;
        const values = parseAttributeValues(document.getElementById("attr-values").value, displayType);
        const payload = {
            name: name,
            slug: document.getElementById("attr-slug").value.trim() || defaultAttrSlug(name),
            display_type: displayType,
            button_style:
                displayType === "button"
                    ? document.getElementById("attr-button-style").value
                    : "",
            values: values,
        };
        const saveAttrBtn = document.getElementById("attr-save");
        api.setBusy(saveAttrBtn, true, "در حال ثبت...");
        api.apiFetch("/api/v1/store-admin/products/attributes", {
            method: "POST",
            body: JSON.stringify(payload),
        }).then(function ({ ok, data }) {
            api.setBusy(saveAttrBtn, false);
            if (!ok) {
                api.flash(data.detail || "ثبت ویژگی ناموفق", true);
                return;
            }
            api.flash("ویژگی ثبت شد");
            attributes.push(data);
            document.getElementById("attr-name").value = "";
            document.getElementById("attr-slug").value = "";
            document.getElementById("attr-slug").dataset.touched = "";
            document.getElementById("attr-values").value = "";
            document.getElementById("attr-create-form").hidden = true;
            renderAttributesSummary();
            refreshVariantAttrSelects();
            syncVariantsEmpty();
        });
    });

    document.getElementById("picker-close").addEventListener("click", closePicker);
    const pickerCancel = document.getElementById("picker-cancel");
    if (pickerCancel) pickerCancel.addEventListener("click", closePicker);
    const pickerConfirm = document.getElementById("picker-confirm");
    if (pickerConfirm) {
        pickerConfirm.addEventListener("click", function () {
            const chosen = pickerSelected.slice();
            if (!chosen.length) {
                api.flash("حداقل یک تصویر انتخاب کنید", true);
                return;
            }
            let added = 0;
            chosen.forEach(function (item) {
                if (applyPickedUrl(item.url, item.alt)) added += 1;
            });
            closePicker();
            if (added) api.flash(api.formatNumber(added) + " تصویر به گالری اضافه شد");
            else api.flash("این تصاویر از قبل در گالری هستند", true);
        });
    }
    document.getElementById("picker-upload-btn").addEventListener("click", function () {
        pickerFileInput.click();
    });
    pickerFileInput.addEventListener("change", function () {
        const files = Array.from(pickerFileInput.files || []);
        if (!files.length) return;
        const uploadBtn = document.getElementById("picker-upload-btn");
        api.setBusy(uploadBtn, true, "آپلود...");
        api.flash("در حال آپلود...");
        let lastError = "";
        let chain = Promise.resolve([]);
        files.forEach(function (file, index) {
            chain = chain.then(function (acc) {
                const fd = new FormData();
                fd.append("file", file);
                fd.append("folder", "products");
                fd.append("title", file.name);
                fd.append("alt_text", "");
                fd.append("is_public", "true");
                if (files.length > 1) {
                    api.flash(
                        "آپلود " +
                            api.formatNumber(index + 1) +
                            " از " +
                            api.formatNumber(files.length) +
                            "..."
                    );
                }
                return api.apiFetch("/api/v1/store-admin/files/upload", { method: "POST", body: fd }).then(
                    function ({ ok, data }) {
                        if (ok) acc.push(data);
                        else lastError = api.errorDetail(data, "آپلود ناموفق");
                        return acc;
                    }
                );
            });
        });
        chain.then(function (uploaded) {
            api.setBusy(uploadBtn, false);
            pickerFileInput.value = "";
            if (!uploaded.length) {
                api.flash(lastError || "آپلود ناموفق", true);
                return;
            }
            let added = 0;
            uploaded.forEach(function (data) {
                if (applyPickedUrl(data.url, data.alt_text || data.title || "")) added += 1;
            });
            closePicker();
            if (added) api.flash(api.formatNumber(added) + " تصویر آپلود و اضافه شد");
            else api.flash("آپلود شد");
        }).catch(function () {
            api.setBusy(uploadBtn, false);
            pickerFileInput.value = "";
            api.flash("آپلود ناموفق", true);
        });
    });
    pickerGrid.addEventListener("click", function (e) {
        const btn = e.target.closest(".sa-picker-item");
        if (!btn) return;
        const url = btn.getAttribute("data-url") || "";
        const alt = btn.getAttribute("data-alt") || "";
        if (!isGalleryPicker()) {
            applyPickedUrl(url, alt);
            closePicker();
            api.flash("تصویر انتخاب شد");
            return;
        }
        const idx = pickerSelected.findIndex(function (item) {
            return item.url === url;
        });
        if (idx >= 0) pickerSelected.splice(idx, 1);
        else pickerSelected.push({ url: url, alt: alt });
        syncPickerSelection();
    });

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const id = document.getElementById("product-id").value;
        const name = document.getElementById("product-name").value.trim();
        const slug = document.getElementById("product-slug").value.trim();
        if (!name) {
            api.flash("نام محصول الزامی است", true);
            document.getElementById("product-name").focus();
            return;
        }
        if (!slug || !/^[a-z0-9\-]+$/.test(slug)) {
            api.flash("اسلاگ را با حروف انگلیسی، عدد و خط تیره وارد کنید", true);
            document.getElementById("product-slug").focus();
            return;
        }
        const categoryVal = document.getElementById("product-category").value;
        const brandVal = document.getElementById("product-brand").value;
        const compareVal = document.getElementById("product-compare").value;
        const productType = document.getElementById("product-type").value;
        const saveBtn = document.getElementById("product-save");
        const payload = {
            name: name,
            slug: slug,
            product_type: productType,
            base_price: Number(document.getElementById("product-price").value || 0),
            compare_price: compareVal === "" ? null : Number(compareVal),
            sku: document.getElementById("product-sku").value.trim(),
            status: document.getElementById("product-status").value,
            short_description: document.getElementById("product-short").value.trim(),
            description: rte ? rte.getContent("#product-description") : document.getElementById("product-description").value.trim(),
            category_id: categoryVal ? Number(categoryVal) : null,
            brand_id: brandVal ? Number(brandVal) : null,
            is_featured: document.getElementById("product-featured").checked,
            tags: collectTags(),
            images: collectImages(),
            meta_title: document.getElementById("product-meta-title").value.trim(),
            meta_description: document.getElementById("product-meta-description").value.trim(),
            meta_keywords: document.getElementById("product-meta-keywords").value.trim(),
            og_image: document.getElementById("product-og-image").value.trim(),
        };

        if (productType === "variable") {
            payload.variants = collectVariants();
            if (!payload.variants.length) {
                api.flash("برای محصول متغیر حداقل یک واریانت لازم است", true);
                return;
            }
        } else {
            payload.initial_stock = Number(document.getElementById("product-stock").value || 0);
            payload.stock = payload.initial_stock;
            payload.variants = [];
        }

        let path = "/api/v1/store-admin/products/";
        let method = "POST";
        if (id) {
            path = path + id;
            method = "PUT";
        }

        api.setBusy(saveBtn, true, "در حال ذخیره...");
        api.setPageLoading(root, true, "در حال ذخیره...");
        api.apiFetch(path, { method: method, body: JSON.stringify(payload) }).then(function ({ ok, data }) {
            api.setBusy(saveBtn, false);
            api.setPageLoading(root, false);
            if (!ok) {
                api.flash(api.errorDetail(data, "ذخیره ناموفق"), true);
                return;
            }
            api.flash(id ? "محصول به‌روز شد" : "محصول ایجاد شد");
            if (!id && data && data.id) {
                window.location.href = "/manage/products/" + data.id + "/edit/";
            } else {
                window.location.href = "/manage/products/";
            }
        }).catch(function () {
            api.setBusy(saveBtn, false);
            api.setPageLoading(root, false);
            api.flash("ذخیره ناموفق", true);
        });
    });

    api.setPageLoading(root, true);
    loadMeta().then(function () {
        const ready = rte
            ? rte.loadShortcodes(api).then(function (shortcodes) {
                return rte.init("#product-description", { shortcodes: shortcodes, height: 320 });
            })
            : Promise.resolve();
        return ready.then(function () {
            if (isEdit && productIdAttr) {
                initEdit(productIdAttr);
            } else {
                initCreate();
            }
        });
    });
})();
