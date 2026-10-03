/**
 * Persist login tokens across tabs and browser restarts, and renew the
 * access token with the refresh token instead of dropping the session.
 */
(function (global) {
    var ACCESS = "access_token";
    var REFRESH = "refresh_token";
    var refreshing = null;

    function read(storage, key) {
        try {
            return storage.getItem(key) || "";
        } catch (e) {
            return "";
        }
    }

    function write(storage, key, value) {
        try {
            if (value) storage.setItem(key, value);
            else storage.removeItem(key);
        } catch (e) {}
    }

    function get(key) {
        var value = read(localStorage, key);
        if (!value) {
            value = read(sessionStorage, key);
            if (value) {
                write(localStorage, key, value);
                write(sessionStorage, key, "");
            }
        }
        return value;
    }

    function setTokens(data) {
        if (!data) return;
        if (data.access_token) {
            write(localStorage, ACCESS, data.access_token);
            write(sessionStorage, ACCESS, "");
        }
        if (data.refresh_token) {
            write(localStorage, REFRESH, data.refresh_token);
            write(sessionStorage, REFRESH, "");
        }
    }

    function clear() {
        write(localStorage, ACCESS, "");
        write(localStorage, REFRESH, "");
        write(sessionStorage, ACCESS, "");
        write(sessionStorage, REFRESH, "");
    }

    function csrfHeader() {
        var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        var headers = { Accept: "application/json", "Content-Type": "application/json" };
        if (match) headers["X-CSRFToken"] = decodeURIComponent(match[1]);
        return headers;
    }

    function refresh() {
        if (refreshing) return refreshing;
        var token = get(REFRESH);
        if (!token) return Promise.resolve(false);
        refreshing = fetch("/api/v1/auth/token/refresh", {
            method: "POST",
            credentials: "same-origin",
            headers: csrfHeader(),
            body: JSON.stringify({ refresh_token: token }),
        })
            .then(function (res) {
                return res.json().catch(function () {
                    return {};
                }).then(function (data) {
                    if (!res.ok || !data.access_token) {
                        clear();
                        return false;
                    }
                    setTokens(data);
                    return true;
                });
            })
            .catch(function () {
                return false;
            })
            .finally(function () {
                refreshing = null;
            });
        return refreshing;
    }

    global.AuthSession = {
        getAccess: function () {
            return get(ACCESS);
        },
        getRefresh: function () {
            return get(REFRESH);
        },
        setTokens: setTokens,
        clear: clear,
        refresh: refresh,
    };
})(window);
