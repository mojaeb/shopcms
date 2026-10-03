(function () {
    const root = document.getElementById("sa-settings");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/settings/")) return;

    const form = document.getElementById("settings-form");
    const gscForm = document.getElementById("seo-gsc-form");
    const themeForm = document.getElementById("theme-settings-form");
    const slidesEl = document.getElementById("theme-slides");
    const slideTpl = document.getElementById("theme-slide-template");
    const picker = document.getElementById("settings-picker");
    const pickerGrid = document.getElementById("settings-picker-grid");
    let pickTarget = null;

    const COLOR_PAIRS = [
        ["theme-color-primary", "theme-color-primary-picker"],
        ["theme-color-bg", "theme-color-bg-picker"],
        ["theme-color-text", "theme-color-text-picker"],
    ];
    const IMAGE_PREVIEWS = [
        ["theme-logo", "theme-logo-preview"],
        ["theme-enamad-image", "theme-enamad-preview"],
        ["theme-badge2-image", "theme-badge2-preview"],
    ];

    function previewStyle(url) {
        const safe = String(url || "").replace(/["\\\n\r]/g, "");
        return safe ? 'url("' + safe + '")' : "";
    }

    function hexOrEmpty(value) {
        const text = String(value || "").trim();
        if (/^#[0-9a-fA-F]{6}$/.test(text)) return text.toLowerCase();
        return "";
    }

    function bindColorPair(textId, pickerId) {
        const text = document.getElementById(textId);
        const swatch = document.getElementById(pickerId);
        if (!text || !swatch || text.dataset.bound) return;
        text.dataset.bound = "1";
        text.addEventListener("input", function () {
            const hex = hexOrEmpty(text.value);
            if (hex) swatch.value = hex;
        });
        swatch.addEventListener("input", function () {
            text.value = swatch.value;
        });
    }

    function syncColorPair(textId, pickerId) {
        const text = document.getElementById(textId);
        const swatch = document.getElementById(pickerId);
        if (!text || !swatch) return;
        const hex = hexOrEmpty(text.value);
        if (hex) swatch.value = hex;
    }

    function syncImagePreview(inputId, wrapId) {
        const input = document.getElementById(inputId);
        const wrap = document.getElementById(wrapId);
        if (!input || !wrap) return;
        const url = (input.value || "").trim();
        if (!url) {
            wrap.hidden = true;
            wrap.style.backgroundImage = "";
            return;
        }
        wrap.style.backgroundImage = previewStyle(url);
        wrap.hidden = false;
    }

    function syncSlidePreview(fieldset) {
        const input = fieldset.querySelector('[name="image"]');
        const wrap = fieldset.querySelector(".js-slide-preview");
        if (!input || !wrap) return;
        const url = (input.value || "").trim();
        if (!url) {
            wrap.hidden = true;
            wrap.style.backgroundImage = "";
            return;
        }
        wrap.style.backgroundImage = previewStyle(url);
        wrap.hidden = false;
    }

    function showPanel(name) {
        root.querySelectorAll(".sa-tab").forEach(function (tab) {
            const on = tab.getAttribute("data-panel") === name;
            tab.classList.toggle("is-active", on);
            tab.setAttribute("aria-selected", on ? "true" : "false");
        });
        const themeFormVisible = name === "look" || name === "badges";
        root.querySelectorAll("[data-panel]").forEach(function (panel) {
            if (panel.classList.contains("sa-tab")) return;
            const key = panel.getAttribute("data-panel");
            const show = key === name || (themeFormVisible && key === "look");
            panel.hidden = !show;
        });
        themeForm.querySelectorAll("[data-section]").forEach(function (section) {
            section.hidden = section.getAttribute("data-section") !== name;
        });
        if (name !== "look" && name !== "badges") {
            themeForm.querySelectorAll("[data-section]").forEach(function (section) {
                section.hidden = true;
            });
        }
    }

    let themeState = {
        logo: "",
        colors: { primary: "#0f766e", background: "#f8fafc", text: "#0f172a" },
        hero: { slides: [] },
        trust_badges: {
            enamad: { image: "", link: "" },
            badge2: { image: "", link: "" },
        },
    };

    function emptySlide() {
        return {
            image: "",
            thumbnail: "",
            title: "",
            text: "",
            button_text: "خرید کنید",
            button_link: "/products/",
            background_color: "#f6f4f1",
        };
    }

    function renumberSlides() {
        slidesEl.querySelectorAll(".sa-theme-slide").forEach(function (el, i) {
            const legend = el.querySelector(".sa-theme-slide-legend");
            if (legend) legend.textContent = "اسلاید " + (i + 1);
        });
    }

    function addSlide(data) {
        const slide = Object.assign(emptySlide(), data || {});
        const node = slideTpl.content.cloneNode(true);
        const fieldset = node.querySelector(".sa-theme-slide");
        fieldset.querySelector('[name="image"]').value = slide.image || "";
        fieldset.querySelector('[name="thumbnail"]').value = slide.thumbnail || "";
        fieldset.querySelector('[name="title"]').value = slide.title || "";
        fieldset.querySelector('[name="text"]').value = slide.text || "";
        fieldset.querySelector('[name="button_text"]').value = slide.button_text || "";
        fieldset.querySelector('[name="button_link"]').value = slide.button_link || "";
        const bg = fieldset.querySelector('[name="background_color"]');
        const bgPicker = fieldset.querySelector('[name="background_picker"]');
        bg.value = slide.background_color || "#f6f4f1";
        const bgHex = hexOrEmpty(bg.value);
        if (bgHex) bgPicker.value = bgHex;
        bg.addEventListener("input", function () {
            const hex = hexOrEmpty(bg.value);
            if (hex) bgPicker.value = hex;
        });
        bgPicker.addEventListener("input", function () {
            bg.value = bgPicker.value;
        });
        const imageInput = fieldset.querySelector('[name="image"]');
        imageInput.addEventListener("input", function () {
            syncSlidePreview(fieldset);
        });
        fieldset.querySelector(".js-pick-slide").addEventListener("click", function () {
            openPicker(imageInput);
        });
        fieldset.querySelector(".theme-remove-slide").addEventListener("click", function () {
            fieldset.remove();
            renumberSlides();
        });
        slidesEl.appendChild(node);
        syncSlidePreview(fieldset);
        renumberSlides();
    }

    function collectSlides() {
        return Array.from(slidesEl.querySelectorAll(".sa-theme-slide")).map(function (el) {
            return {
                image: el.querySelector('[name="image"]').value.trim(),
                thumbnail: el.querySelector('[name="thumbnail"]').value.trim(),
                title: el.querySelector('[name="title"]').value.trim(),
                text: el.querySelector('[name="text"]').value.trim(),
                button_text: el.querySelector('[name="button_text"]').value.trim(),
                button_link: el.querySelector('[name="button_link"]').value.trim() || "/products/",
                background_color: el.querySelector('[name="background_color"]').value.trim() || "#f6f4f1",
            };
        });
    }

    function renderThemeForm(theme) {
        themeState = {
            logo: (theme && theme.logo) || "",
            colors: Object.assign(
                { primary: "#0f766e", background: "#f8fafc", text: "#0f172a" },
                (theme && theme.colors) || {}
            ),
            hero: { slides: ((theme && theme.hero && theme.hero.slides) || []).slice() },
            trust_badges: {
                enamad: Object.assign(
                    { image: "", link: "" },
                    (theme && theme.trust_badges && theme.trust_badges.enamad) || {}
                ),
                badge2: Object.assign(
                    { image: "", link: "" },
                    (theme && theme.trust_badges && theme.trust_badges.badge2) || {}
                ),
            },
        };
        document.getElementById("theme-logo").value = themeState.logo;
        document.getElementById("theme-color-primary").value = themeState.colors.primary || "";
        document.getElementById("theme-color-bg").value = themeState.colors.background || "";
        document.getElementById("theme-color-text").value = themeState.colors.text || "";
        document.getElementById("theme-enamad-image").value = themeState.trust_badges.enamad.image || "";
        document.getElementById("theme-enamad-link").value = themeState.trust_badges.enamad.link || "";
        document.getElementById("theme-badge2-image").value = themeState.trust_badges.badge2.image || "";
        document.getElementById("theme-badge2-link").value = themeState.trust_badges.badge2.link || "";
        COLOR_PAIRS.forEach(function (pair) {
            syncColorPair(pair[0], pair[1]);
        });
        IMAGE_PREVIEWS.forEach(function (row) {
            syncImagePreview(row[0], row[1]);
        });
        slidesEl.innerHTML = "";
        if (themeState.hero.slides.length) {
            themeState.hero.slides.forEach(addSlide);
        }
    }

    function renderGscForm(seo) {
        const token = (seo && seo.google_site_verification) || "";
        const htmlFile = (seo && seo.google_html_file) || "";
        const verificationEl = document.getElementById("gsc-verification");
        const sitemapEl = document.getElementById("gsc-sitemap");
        const robotsEl = document.getElementById("gsc-robots");
        const htmlFileEl = document.getElementById("gsc-html-file");
        const htmlWrap = document.getElementById("gsc-html-file-wrap");
        const statusEl = document.getElementById("gsc-status");
        if (verificationEl) verificationEl.value = token || htmlFile || "";
        if (sitemapEl) sitemapEl.value = (seo && seo.sitemap_url) || (window.location.origin + "/sitemap.xml");
        if (robotsEl) robotsEl.value = (seo && seo.robots_url) || (window.location.origin + "/robots.txt");
        if (htmlFileEl) htmlFileEl.value = (seo && seo.html_file_url) || "";
        if (htmlWrap) htmlWrap.hidden = !htmlFile;
        if (statusEl) {
            const on = !!(seo && seo.verification_configured);
            statusEl.hidden = false;
            statusEl.classList.toggle("is-on", on);
            statusEl.classList.toggle("is-off", !on);
            statusEl.textContent = on
                ? "کد تأیید ذخیره شد. در گوگل کنسول Verify را بزنید."
                : "هنوز وصل نشده.";
        }
    }

    function copyField(id) {
        const el = document.getElementById(id);
        const text = el && el.value ? el.value : "";
        if (!text) return;
        const done = function () {
            api.flash("کپی شد");
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(done).catch(function () {
                el.select();
                document.execCommand("copy");
                done();
            });
            return;
        }
        el.select();
        document.execCommand("copy");
        done();
    }

    function loadSettings() {
        api.setPageLoading(root, true);
        api.apiFetch("/api/v1/store-admin/settings").then(function ({ ok, data }) {
            api.setPageLoading(root, false);
            if (!ok) {
                api.flash(data.detail || "خطا در بارگذاری تنظیمات", true);
                return;
            }
            const general = data.general || {};
            document.getElementById("setting-name").value = general.name || "";
            document.getElementById("setting-currency").value = general.currency || "";
            document.getElementById("setting-timezone").value = general.timezone || "";
            document.getElementById("setting-language").value = general.language || "";
            renderThemeForm(data.theme || {});
            renderGscForm(data.seo || {});
        });
    }

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        const payload = {
            name: document.getElementById("setting-name").value.trim(),
            currency: document.getElementById("setting-currency").value.trim(),
            timezone: document.getElementById("setting-timezone").value.trim() || null,
            language: document.getElementById("setting-language").value.trim() || null,
        };
        api.setBusy(btn, true, "در حال ذخیره...");
        api.setPageLoading(root, true, "در حال ذخیره...");
        api.apiFetch("/api/v1/store-admin/settings/general", {
            method: "PUT",
            body: JSON.stringify(payload),
        }).then(function ({ ok, data }) {
            api.setBusy(btn, false);
            api.setPageLoading(root, false);
            if (!ok) {
                api.flash(data.detail || "ذخیره ناموفق", true);
                return;
            }
            api.flash("تنظیمات ذخیره شد");
            if (data.name) document.getElementById("setting-name").value = data.name;
        });
    });

    if (gscForm) {
        gscForm.querySelectorAll("[data-copy]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                copyField(btn.getAttribute("data-copy"));
            });
        });
        gscForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const btn = gscForm.querySelector('button[type="submit"]');
            const payload = {
                google_site_verification: document.getElementById("gsc-verification").value.trim(),
            };
            api.setBusy(btn, true, "در حال ذخیره...");
            api.setPageLoading(root, true, "در حال ذخیره...");
            api.apiFetch("/api/v1/store-admin/settings/seo", {
                method: "PUT",
                body: JSON.stringify(payload),
            }).then(function ({ ok, data }) {
                api.setBusy(btn, false);
                api.setPageLoading(root, false);
                if (!ok) {
                    api.flash(data.detail || "ذخیره اتصال گوگل ناموفق", true);
                    return;
                }
                api.flash("اتصال گوگل ذخیره شد");
                renderGscForm(data);
            });
        });
    }

    function thumbUrl(file) {
        const thumbs = (file && file.thumbnails) || [];
        const prefer = thumbs.find(function (t) {
            return t.variant === "small" || t.variant === "thumb";
        });
        return (prefer && prefer.url) || (file && file.url) || "";
    }

    function closePicker() {
        pickTarget = null;
        if (picker && typeof picker.close === "function") picker.close();
    }

    function openPicker(input) {
        if (!picker || !input) return;
        pickTarget = input;
        if (typeof picker.showModal === "function") picker.showModal();
        pickerGrid.innerHTML = api.loadingHtml(null, { compact: true });
        api.apiFetch("/api/v1/store-admin/files?file_type=image&page=1").then(function (res) {
            if (!res.ok) {
                pickerGrid.innerHTML =
                    '<div class="sa-empty">' +
                    api.escapeHtml((res.data && res.data.detail) || "خطا در دریافت رسانه") +
                    "</div>";
                return;
            }
            const files = api.unwrapList(res.data);
            if (!files.length) {
                pickerGrid.innerHTML = '<div class="sa-empty">تصویری نیست. از بخش رسانه آپلود کنید.</div>';
                return;
            }
            pickerGrid.innerHTML = files
                .map(function (file) {
                    const url = file.url || "";
                    return (
                        '<button type="button" class="sa-picker-item" data-url="' +
                        api.escapeHtml(url) +
                        '"><img src="' +
                        api.escapeHtml(thumbUrl(file) || url) +
                        '" alt=""><span>' +
                        api.escapeHtml(file.title || file.original_name || "تصویر") +
                        "</span></button>"
                    );
                })
                .join("");
        });
    }

    root.querySelectorAll(".sa-tab").forEach(function (tab) {
        tab.addEventListener("click", function () {
            showPanel(tab.getAttribute("data-panel"));
        });
    });

    COLOR_PAIRS.forEach(function (pair) {
        bindColorPair(pair[0], pair[1]);
    });
    IMAGE_PREVIEWS.forEach(function (row) {
        const input = document.getElementById(row[0]);
        if (!input) return;
        input.addEventListener("input", function () {
            syncImagePreview(row[0], row[1]);
        });
    });
    root.querySelectorAll("[data-pick]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            openPicker(document.getElementById(btn.getAttribute("data-pick")));
        });
    });
    document.getElementById("settings-picker-close").addEventListener("click", closePicker);
    pickerGrid.addEventListener("click", function (e) {
        const btn = e.target.closest(".sa-picker-item");
        if (!btn || !pickTarget) return;
        pickTarget.value = btn.getAttribute("data-url") || "";
        pickTarget.dispatchEvent(new Event("input", { bubbles: true }));
        closePicker();
    });

    document.getElementById("theme-add-slide").addEventListener("click", function () {
        showPanel("look");
        addSlide(emptySlide());
    });

    themeForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const btn = themeForm.querySelector('button[type="submit"]');
        const payload = {
            logo: document.getElementById("theme-logo").value.trim(),
            colors: {
                primary: document.getElementById("theme-color-primary").value.trim() || "#0f766e",
                background: document.getElementById("theme-color-bg").value.trim() || "#f8fafc",
                text: document.getElementById("theme-color-text").value.trim() || "#0f172a",
            },
            trust_badges: {
                enamad: {
                    image: document.getElementById("theme-enamad-image").value.trim(),
                    link: document.getElementById("theme-enamad-link").value.trim(),
                },
                badge2: {
                    image: document.getElementById("theme-badge2-image").value.trim(),
                    link: document.getElementById("theme-badge2-link").value.trim(),
                },
            },
            hero: {
                slides: collectSlides(),
            },
        };
        api.setBusy(btn, true, "در حال ذخیره...");
        api.setPageLoading(root, true, "در حال ذخیره...");
        api.apiFetch("/api/v1/store-admin/settings/theme", {
            method: "PUT",
            body: JSON.stringify(payload),
        }).then(function ({ ok, data }) {
            api.setBusy(btn, false);
            api.setPageLoading(root, false);
            if (!ok) {
                api.flash(data.detail || "ذخیره تنظیمات تم ناموفق", true);
                return;
            }
            api.flash("تنظیمات تم ذخیره شد");
            renderThemeForm(data);
        });
    });

    loadSettings();
})();
