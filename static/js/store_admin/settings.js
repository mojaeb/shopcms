(function () {
    const root = document.getElementById("sa-settings");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/settings/")) return;

    const form = document.getElementById("settings-form");
    const themeForm = document.getElementById("theme-settings-form");
    const loading = document.getElementById("settings-loading");
    const slidesEl = document.getElementById("theme-slides");
    const slideTpl = document.getElementById("theme-slide-template");

    let themeState = {
        logo: "",
        colors: { primary: "#111111", background: "#ffffff", text: "#111111" },
        hero: { slides: [] },
    };

    function emptySlide() {
        return {
            image: "",
            thumbnail: "",
            title: "",
            text: "",
            button_text: "خرید کنید",
            button_link: "/category/",
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
                button_link: el.querySelector('[name="button_link"]').value.trim() || "/category/",
                background_color: el.querySelector('[name="background_color"]').value.trim() || "#f6f4f1",
            };
        });
    }

    function renderThemeForm(theme) {
        themeState = {
            logo: (theme && theme.logo) || "",
            colors: Object.assign(
                { primary: "#111111", background: "#ffffff", text: "#111111" },
                (theme && theme.colors) || {}
            ),
            hero: { slides: ((theme && theme.hero && theme.hero.slides) || []).slice() },
        };
        document.getElementById("theme-logo").value = themeState.logo;
        document.getElementById("theme-color-primary").value = themeState.colors.primary || "";
        document.getElementById("theme-color-bg").value = themeState.colors.background || "";
        document.getElementById("theme-color-text").value = themeState.colors.text || "";
        slidesEl.innerHTML = "";
        if (themeState.hero.slides.length) {
            themeState.hero.slides.forEach(addSlide);
        }
        themeForm.hidden = false;
    }

    function loadSettings() {
        api.apiFetch("/api/v1/store-admin/settings").then(function ({ ok, data }) {
            loading.hidden = true;
            if (!ok) {
                api.flash(data.detail || "خطا در بارگذاری تنظیمات", true);
                return;
            }
            const general = data.general || {};
            document.getElementById("setting-name").value = general.name || "";
            document.getElementById("setting-currency").value = general.currency || "";
            document.getElementById("setting-timezone").value = general.timezone || "";
            document.getElementById("setting-language").value = general.language || "";
            form.hidden = false;
            renderThemeForm(data.theme || {});
        });
    }

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const payload = {
            name: document.getElementById("setting-name").value.trim(),
            currency: document.getElementById("setting-currency").value.trim(),
            timezone: document.getElementById("setting-timezone").value.trim() || null,
            language: document.getElementById("setting-language").value.trim() || null,
        };
        api.apiFetch("/api/v1/store-admin/settings/general", {
            method: "PUT",
            body: JSON.stringify(payload),
        }).then(function ({ ok, data }) {
            if (!ok) {
                api.flash(data.detail || "ذخیره ناموفق", true);
                return;
            }
            api.flash("تنظیمات ذخیره شد");
            if (data.name) document.getElementById("setting-name").value = data.name;
        });
    });

    document.getElementById("theme-add-slide").addEventListener("click", function () {
        addSlide(emptySlide());
    });

    themeForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const payload = {
            logo: document.getElementById("theme-logo").value.trim(),
            colors: {
                primary: document.getElementById("theme-color-primary").value.trim() || "#111111",
                background: document.getElementById("theme-color-bg").value.trim() || "#ffffff",
                text: document.getElementById("theme-color-text").value.trim() || "#111111",
            },
            hero: {
                slides: collectSlides(),
            },
        };
        api.apiFetch("/api/v1/store-admin/settings/theme", {
            method: "PUT",
            body: JSON.stringify(payload),
        }).then(function ({ ok, data }) {
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
