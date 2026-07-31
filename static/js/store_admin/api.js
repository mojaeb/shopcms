/**
 * Shared Store Admin API client (Bearer JWT).
 */
(function (global) {
    const ACCESS_KEY = "access_token";
    const REFRESH_KEY = "refresh_token";
    const LOADING_MSG = "در حال بارگذاری...";

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : "";
    }

    function getToken() {
        return sessionStorage.getItem(ACCESS_KEY) || "";
    }

    function requireAuth(nextPath) {
        if (getToken()) return true;
        const next = encodeURIComponent(nextPath || window.location.pathname);
        window.location.href = "/login/?next=" + next;
        return false;
    }

    function flash(message, isError) {
        const el = document.getElementById("sa-flash");
        if (!el) return;
        el.hidden = !message;
        el.textContent = message || "";
        el.classList.toggle("is-error", !!isError);
        el.classList.toggle("is-ok", !isError && !!message);
    }

    function logout() {
        const refresh = sessionStorage.getItem(REFRESH_KEY);
        const access = sessionStorage.getItem(ACCESS_KEY);
        sessionStorage.removeItem(ACCESS_KEY);
        sessionStorage.removeItem(REFRESH_KEY);
        const headers = { Accept: "application/json", "Content-Type": "application/json" };
        const csrf = getCookie("csrftoken");
        if (csrf) headers["X-CSRFToken"] = csrf;
        if (access) headers.Authorization = "Bearer " + access;
        fetch("/api/v1/auth/logout", {
            method: "POST",
            credentials: "same-origin",
            headers,
            body: JSON.stringify({ refresh_token: refresh || "" }),
        }).finally(function () {
            window.location.href = "/login/?next=/manage/";
        });
    }

    function unwrapList(data) {
        if (Array.isArray(data)) return data;
        if (data && Array.isArray(data.items)) return data.items;
        return [];
    }

    function escapeHtml(str) {
        return String(str == null ? "" : str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function formatNumber(n) {
        try {
            return Number(n).toLocaleString("fa-IR");
        } catch (e) {
            return String(n);
        }
    }

    /** Spinner markup for AJAX regions. */
    function loadingHtml(message, opts) {
        opts = opts || {};
        const msg = message || LOADING_MSG;
        const cls =
            "sa-loading" +
            (opts.inline ? " sa-loading--inline" : "") +
            (opts.compact ? " sa-loading--compact" : "");
        const inner = '<div class="' + cls + '" role="status" aria-live="polite">' + escapeHtml(msg) + "</div>";
        if (opts.cols) {
            return (
                '<tr class="sa-loading-row"><td colspan="' +
                Number(opts.cols) +
                '">' +
                inner +
                "</td></tr>"
            );
        }
        return inner;
    }

    function setLoading(el, message, opts) {
        if (!el) return;
        el.innerHTML = loadingHtml(message, opts);
    }

    /** Disable button and show busy label while a mutation runs. */
    function setBusy(el, busy, busyLabel) {
        if (!el) return;
        if (busy) {
            if (el.dataset.saLabel == null) el.dataset.saLabel = el.textContent;
            el.disabled = true;
            el.classList.add("is-busy");
            el.setAttribute("aria-busy", "true");
            if (busyLabel) el.textContent = busyLabel;
        } else {
            el.disabled = false;
            el.classList.remove("is-busy");
            el.removeAttribute("aria-busy");
            if (el.dataset.saLabel != null) {
                el.textContent = el.dataset.saLabel;
                delete el.dataset.saLabel;
            }
        }
    }

    /** Show/hide a dedicated loading element and related form chrome. */
    function toggleFormLoading(loadingEl, show, extras) {
        extras = extras || {};
        if (loadingEl) loadingEl.hidden = !show;
        (extras.hideWhileLoading || []).forEach(function (node) {
            if (node) node.hidden = !!show;
        });
        (extras.showWhenReady || []).forEach(function (node) {
            if (node) node.hidden = !!show;
        });
    }

    /** Overlay loader fixed to the viewport (main pane). Scroll-safe. */
    var pageLoadingDepth = 0;
    var pageLoadingHosts = [];

    function getGlobalOverlay() {
        var overlay = document.getElementById("sa-global-overlay");
        if (!overlay) {
            overlay = document.createElement("div");
            overlay.id = "sa-global-overlay";
            overlay.className = "sa-page-overlay";
            overlay.hidden = true;
            overlay.setAttribute("role", "status");
            overlay.setAttribute("aria-live", "polite");
            document.body.appendChild(overlay);
        }
        return overlay;
    }

    function setPageLoading(host, show, message) {
        var overlay = getGlobalOverlay();
        if (show) {
            pageLoadingDepth += 1;
            if (host && pageLoadingHosts.indexOf(host) === -1) {
                pageLoadingHosts.push(host);
                host.classList.add("sa-loading-host", "is-loading");
            }
            overlay.innerHTML = loadingHtml(message || LOADING_MSG, { compact: true });
            overlay.hidden = false;
            document.body.classList.add("is-sa-loading");
        } else {
            pageLoadingDepth = Math.max(0, pageLoadingDepth - 1);
            if (host) {
                host.classList.remove("is-loading");
                pageLoadingHosts = pageLoadingHosts.filter(function (h) {
                    return h !== host;
                });
            }
            if (pageLoadingDepth === 0) {
                overlay.hidden = true;
                overlay.innerHTML = "";
                document.body.classList.remove("is-sa-loading");
                pageLoadingHosts.forEach(function (h) {
                    h.classList.remove("is-loading");
                });
                pageLoadingHosts = [];
            }
        }
    }

    function apiFetch(path, options) {
        options = options || {};
        const token = getToken();
        if (!token) {
            requireAuth(window.location.pathname);
            return Promise.resolve({ ok: false, status: 401, data: { detail: "Unauthorized" } });
        }

        const headers = {
            Accept: "application/json",
            ...(options.headers || {}),
        };
        if (!(options.body instanceof FormData)) {
            headers["Content-Type"] = headers["Content-Type"] || "application/json";
        }
        headers.Authorization = "Bearer " + token;
        const csrf = getCookie("csrftoken");
        if (csrf) headers["X-CSRFToken"] = csrf;

        return fetch(path, {
            credentials: "same-origin",
            ...options,
            headers,
        }).then(async function (res) {
            const data = await res.json().catch(function () {
                return {};
            });
            if (res.status === 401) {
                sessionStorage.removeItem(ACCESS_KEY);
                requireAuth(window.location.pathname);
            }
            return { ok: res.ok, status: res.status, data: data };
        });
    }

    global.StoreAdminApi = {
        getToken: getToken,
        requireAuth: requireAuth,
        apiFetch: apiFetch,
        unwrapList: unwrapList,
        flash: flash,
        logout: logout,
        escapeHtml: escapeHtml,
        formatNumber: formatNumber,
        loadingHtml: loadingHtml,
        setLoading: setLoading,
        setBusy: setBusy,
        toggleFormLoading: toggleFormLoading,
        setPageLoading: setPageLoading,
        LOADING_MSG: LOADING_MSG,
    };
})(window);
