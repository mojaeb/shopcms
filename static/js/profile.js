(function () {
    const root = document.getElementById("profile-edit-page");
    if (!root) return;

    const form = document.getElementById("profile-edit-form");
    const messageEl = document.getElementById("profile-edit-message");
    const saveBtn = document.getElementById("profile-save-btn");
    if (!form) return;

    const API = "/api/v1/auth/me";

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : "";
    }

    function setMessage(text, isError) {
        if (!messageEl) return;
        messageEl.textContent = text || "";
        messageEl.style.color = isError ? "var(--danger, #dc2626)" : "var(--color-accent, #16a34a)";
    }

    function apiPatch(payload) {
        const headers = {
            "Content-Type": "application/json",
            Accept: "application/json",
        };
        const csrf = getCookie("csrftoken");
        if (csrf) headers["X-CSRFToken"] = csrf;
        const access = sessionStorage.getItem("access_token");
        if (access) headers.Authorization = "Bearer " + access;

        return fetch(API, {
            method: "PATCH",
            credentials: "same-origin",
            headers,
            body: JSON.stringify(payload),
        }).then(async (res) => {
            let data = {};
            try {
                data = await res.json();
            } catch (_) {
                data = {};
            }
            return { ok: res.ok, status: res.status, data };
        });
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const firstName = (form.first_name.value || "").trim();
        const lastName = (form.last_name.value || "").trim();
        const email = (form.email.value || "").trim();

        if (!firstName || !lastName) {
            setMessage("نام و نام خانوادگی الزامی است.", true);
            return;
        }

        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.textContent = "در حال ذخیره...";
        }
        setMessage("در حال ذخیره...");

        apiPatch({
            first_name: firstName,
            last_name: lastName,
            email: email,
        }).then(({ ok, status, data }) => {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = "ذخیره تغییرات";
            }
            if (!ok) {
                if (status === 401) {
                    setMessage("نشست منقضی شده. دوباره وارد شوید.", true);
                    return;
                }
                setMessage(data.detail || "خطا در ذخیره پروفایل", true);
                return;
            }
            setMessage("پروفایل با موفقیت ذخیره شد.");
            window.setTimeout(() => {
                window.location.href = "/profile/";
            }, 600);
        }).catch(() => {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.textContent = "ذخیره تغییرات";
            }
            setMessage("ارتباط با سرور برقرار نشد.", true);
        });
    });
})();
