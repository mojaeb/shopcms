/**
 * Shared Store Admin API client (Bearer JWT).
 */
(function (global) {
    const ACCESS_KEY = "access_token";
    const REFRESH_KEY = "refresh_token";

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

    global.StoreAdminApi = {
        getToken: getToken,
        requireAuth: requireAuth,
        apiFetch: apiFetch,
        unwrapList: unwrapList,
        flash: flash,
        logout: logout,
        escapeHtml: escapeHtml,
        formatNumber: formatNumber,
    };
})(window);
