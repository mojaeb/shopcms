(function () {
    const logoutLinks = document.querySelectorAll("#logout-link, .js-logout");
    if (!logoutLinks.length) return;

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : "";
    }

    function logout(event) {
        event.preventDefault();
        const headers = { "Content-Type": "application/json", Accept: "application/json" };
        const csrf = getCookie("csrftoken");
        if (csrf) headers["X-CSRFToken"] = csrf;
        fetch("/api/v1/auth/logout", {
            method: "POST",
            credentials: "same-origin",
            headers,
            body: JSON.stringify({
                refresh_token: window.AuthSession
                    ? window.AuthSession.getRefresh()
                    : sessionStorage.getItem("refresh_token") || "",
            }),
        }).finally(() => {
            if (window.AuthSession) window.AuthSession.clear();
            sessionStorage.removeItem("access_token");
            sessionStorage.removeItem("refresh_token");
            try {
                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");
            } catch (e) {}
            window.location.href = "/";
        });
    }

    logoutLinks.forEach((link) => link.addEventListener("click", logout));
})();
