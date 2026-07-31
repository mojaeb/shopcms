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
            body: JSON.stringify({ refresh_token: sessionStorage.getItem("refresh_token") || "" }),
        }).finally(() => {
            sessionStorage.removeItem("access_token");
            sessionStorage.removeItem("refresh_token");
            window.location.href = "/";
        });
    }

    logoutLinks.forEach((link) => link.addEventListener("click", logout));
})();
