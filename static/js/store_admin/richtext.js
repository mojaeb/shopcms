/**
 * TinyMCE rich-text helper for Store Admin.
 * Loads TinyMCE from CDN once, supports shortcode insert menu.
 */
(function (global) {
    const CDN = "https://cdn.jsdelivr.net/npm/tinymce@7.6.0/tinymce.min.js";
    let loadPromise = null;
    const instances = new Map();

    function loadScript() {
        if (global.tinymce) return Promise.resolve();
        if (loadPromise) return loadPromise;
        loadPromise = new Promise(function (resolve, reject) {
            const s = document.createElement("script");
            s.src = CDN;
            s.referrerPolicy = "origin";
            s.onload = function () { resolve(); };
            s.onerror = function () { reject(new Error("TinyMCE load failed")); };
            document.head.appendChild(s);
        });
        return loadPromise;
    }

    function destroy(selector) {
        const id = selector.replace(/^#/, "");
        if (global.tinymce) {
            const ed = global.tinymce.get(id);
            if (ed) ed.remove();
        }
        instances.delete(id);
    }

    function getContent(selector) {
        const id = selector.replace(/^#/, "");
        if (global.tinymce) {
            const ed = global.tinymce.get(id);
            if (ed) return ed.getContent();
        }
        const el = document.getElementById(id);
        return el ? el.value : "";
    }

    function setContent(selector, html) {
        const id = selector.replace(/^#/, "");
        if (global.tinymce) {
            const ed = global.tinymce.get(id);
            if (ed) {
                ed.setContent(html || "");
                return;
            }
        }
        const el = document.getElementById(id);
        if (el) el.value = html || "";
    }

    function buildShortcodeMenu(shortcodes) {
        const items = (shortcodes || []).map(function (sc) {
            return {
                type: "menuitem",
                text: sc.label + " [" + sc.name + "]",
                onAction: function () {
                    const ed = global.tinymce.activeEditor;
                    if (!ed) return;
                    const sample = sc.example || (
                        sc.is_self_closing
                            ? "[" + sc.name + " /]"
                            : "[" + sc.name + "]\n\n[/" + sc.name + "]"
                    );
                    ed.insertContent(sample.replace(/\n/g, "<br>"));
                },
            };
        });
        return items;
    }

    /**
     * @param {string} selector e.g. "#product-description"
     * @param {object} options
     * @param {Array} [options.shortcodes]
     * @param {number} [options.height]
     */
    function init(selector, options) {
        options = options || {};
        const el = typeof selector === "string"
            ? document.querySelector(selector)
            : selector;
        if (!el) return Promise.resolve(null);
        const id = el.id;
        if (!id) {
            el.id = "rte-" + Math.random().toString(36).slice(2, 9);
        }
        destroy("#" + el.id);

        return loadScript().then(function () {
            const shortcodeItems = buildShortcodeMenu(options.shortcodes || []);
            return global.tinymce.init({
                selector: "#" + el.id,
                license_key: "gpl",
                directionality: "rtl",
                language: undefined,
                height: options.height || 360,
                menubar: "edit insert view format table tools",
                plugins: "lists link image table code fullscreen directionality autoresize",
                toolbar:
                    "undo redo | styles | bold italic underline | " +
                    "alignright aligncenter alignleft | bullist numlist | " +
                    "link image | shortcodes | code fullscreen",
                branding: false,
                promotion: false,
                convert_urls: false,
                relative_urls: false,
                content_style:
                    "body { font-family: Tahoma, Segoe UI, sans-serif; font-size: 14px; direction: rtl; } " +
                    "img { max-width: 100%; height: auto; } " +
                    ".sc-grid { display: grid; gap: 1rem; } " +
                    ".sc-grid-1-2 { grid-template-columns: 1fr 1fr; } " +
                    ".sc-grid-1-3 { grid-template-columns: 1fr 1fr 1fr; }",
                setup: function (editor) {
                    if (shortcodeItems.length) {
                        editor.ui.registry.addMenuButton("shortcodes", {
                            text: "شورت‌کد",
                            fetch: function (callback) {
                                callback(shortcodeItems);
                            },
                        });
                    }
                    instances.set(el.id, editor);
                },
            }).then(function (editors) {
                return editors && editors[0] ? editors[0] : null;
            });
        });
    }

    function loadShortcodes(api) {
        if (!api || !api.apiFetch) return Promise.resolve([]);
        return api.apiFetch("/api/v1/store-admin/cms/shortcodes").then(function (res) {
            if (!res.ok) return [];
            return Array.isArray(res.data) ? res.data : [];
        });
    }

    global.StoreAdminRichText = {
        init: init,
        destroy: destroy,
        getContent: getContent,
        setContent: setContent,
        loadShortcodes: loadShortcodes,
    };
})(window);
