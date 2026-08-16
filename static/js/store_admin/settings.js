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
        fieldset.querySelector('[name="background_color"]').value = slide.background_color || "#f6f4f1";
        fieldset.querySelector(".theme-remove-slide").addEventListener("click", function () {
            fieldset.remove();
            renumberSlides();
        });
        slidesEl.appendChild(node);
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

    document.getElementById("theme-add-slide").addEventListener("click", function () {
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

    const catList = document.getElementById("categories-list");
    const catForm = document.getElementById("category-create-form");

    function renderCategories(cats) {
        if (!catList) return;
        if (!cats.length) {
            catList.innerHTML = '<p class="sa-muted">هنوز دسته‌ای ثبت نشده.</p>';
            return;
        }
        catList.innerHTML = cats
            .map(function (c) {
                return (
                    '<div class="sa-card" style="padding:0.75rem 1rem;margin:0;" data-cat-id="' +
                    c.id +
                    '">' +
                    "<strong>" +
                    api.escapeHtml(c.name) +
                    "</strong> " +
                    '<span class="sa-muted" dir="ltr">' +
                    api.escapeHtml(c.slug) +
                    "</span>" +
                    (c.is_custom
                        ? ' <span class="sa-badge" style="background:#ecfdf5;color:#047857;">سفارشی</span>'
                        : "") +
                    '<div class="sa-form-actions" style="margin-top:0.5rem;">' +
                    '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm cat-toggle-custom" data-id="' +
                    c.id +
                    '" data-custom="' +
                    (c.is_custom ? "1" : "0") +
                    '">' +
                    (c.is_custom ? "حذف پرچم سفارشی" : "علامت به‌عنوان سفارشی") +
                    "</button></div></div>"
                );
            })
            .join("");

        catList.querySelectorAll(".cat-toggle-custom").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const id = btn.dataset.id;
                const next = btn.dataset.custom !== "1";
                api.apiFetch("/api/v1/store-admin/products/categories/" + id, {
                    method: "PATCH",
                    body: JSON.stringify({ is_custom: next }),
                }).then(function ({ ok, data }) {
                    if (!ok) {
                        api.flash(data.detail || "به‌روزرسانی ناموفق", true);
                        return;
                    }
                    api.flash(next ? "دسته سفارشی شد" : "پرچم سفارشی برداشته شد");
                    loadCategories();
                });
            });
        });
    }

    function loadCategories() {
        if (!catList) return;
        api.apiFetch("/api/v1/store-admin/products/categories/list").then(function ({ ok, data }) {
            if (!ok) return;
            renderCategories(api.unwrapList(data));
        });
    }

    if (catForm) {
        catForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const name = document.getElementById("cat-name").value.trim();
            let slug = document.getElementById("cat-slug").value.trim();
            if (!slug && name) {
                slug = name
                    .toLowerCase()
                    .replace(/\s+/g, "-")
                    .replace(/[^a-z0-9\-]/g, "");
            }
            const payload = {
                name: name,
                slug: slug,
                image: document.getElementById("cat-image").value.trim(),
                is_custom: document.getElementById("cat-is-custom").checked,
            };
            const btn = catForm.querySelector('button[type="submit"]');
            api.setBusy(btn, true, "در حال ذخیره...");
            api.apiFetch("/api/v1/store-admin/products/categories", {
                method: "POST",
                body: JSON.stringify(payload),
            }).then(function ({ ok, data }) {
                api.setBusy(btn, false);
                if (!ok) {
                    api.flash(data.detail || "ایجاد دسته ناموفق", true);
                    return;
                }
                api.flash("دسته ایجاد شد");
                catForm.reset();
                loadCategories();
            });
        });
    }

    loadCategories();
})();
