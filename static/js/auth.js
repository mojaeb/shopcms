(function () {
    const root = document.getElementById("auth-page");
    if (!root) return;

    const API = "/api/v1/auth";
    let mode = root.dataset.mode || "login";
    let phone = "";
    let expiresIn = 120;
    let countdownTimer = null;

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : "";
    }

    function apiFetch(path, options = {}) {
        const headers = {
            "Content-Type": "application/json",
            Accept: "application/json",
            ...(options.headers || {}),
        };
        const csrf = getCookie("csrftoken");
        if (csrf) headers["X-CSRFToken"] = csrf;
        return fetch(API + path, {
            credentials: "same-origin",
            ...options,
            headers,
        }).then(async (res) => ({
            ok: res.ok,
            status: res.status,
            data: await res.json().catch(() => ({})),
        }));
    }

    function setMessage(text, isError) {
        const el = document.getElementById("auth-message");
        if (!el) return;
        el.textContent = text || "";
        el.style.color = isError ? "var(--danger, #c0392b)" : "";
    }

    function setMode(nextMode) {
        mode = nextMode;
        root.dataset.mode = mode;
        document.querySelectorAll(".auth-tab").forEach((btn) => {
            btn.classList.toggle("btn", btn.dataset.mode === mode);
            btn.classList.toggle("btn-outline", btn.dataset.mode !== mode);
        });
        document.getElementById("register-fields").style.display = mode === "register" ? "block" : "none";
        const title = mode === "register" ? "ثبت‌نام" : "ورود";
        document.querySelector(".page-title").textContent = title;
        document.title = document.title.replace(/(ورود|ثبت‌نام)/, title);
    }

    function showVerifyStep() {
        document.getElementById("auth-phone-form").style.display = "none";
        document.getElementById("auth-verify-form").style.display = "block";
        document.getElementById("auth-phone-display").textContent = `کد به ${phone} ارسال شد.`;
        document.getElementById("auth-code").focus();
        startCountdown();
    }

    function showPhoneStep() {
        document.getElementById("auth-phone-form").style.display = "block";
        document.getElementById("auth-verify-form").style.display = "none";
        if (countdownTimer) clearInterval(countdownTimer);
        document.getElementById("auth-send-btn").disabled = false;
        document.getElementById("auth-send-btn").textContent = "دریافت کد";
    }

    function startCountdown() {
        let remaining = expiresIn;
        const btn = document.getElementById("auth-send-btn");
        btn.disabled = true;
        btn.textContent = `ارسال مجدد (${remaining})`;
        if (countdownTimer) clearInterval(countdownTimer);
        countdownTimer = setInterval(() => {
            remaining -= 1;
            if (remaining <= 0) {
                clearInterval(countdownTimer);
                btn.disabled = false;
                btn.textContent = "ارسال مجدد کد";
                showPhoneStep();
                return;
            }
            btn.textContent = `ارسال مجدد (${remaining})`;
        }, 1000);
    }

    function getRedirectUrl(loginData) {
        const params = new URLSearchParams(window.location.search);
        const next = params.get("next");
        if (next) return next;
        const staffRoles = [
            "store_admin",
            "manager",
            "content",
            "products",
            "orders",
            "reports",
            "support",
            "super_admin",
        ];
        if (loginData && staffRoles.indexOf(loginData.role) !== -1) {
            return "/manage/";
        }
        return "/dashboard/";
    }

    document.querySelectorAll(".auth-tab").forEach((btn) => {
        btn.addEventListener("click", () => {
            setMode(btn.dataset.mode);
            setMessage("");
            showPhoneStep();
        });
    });

    document.getElementById("auth-back-btn").addEventListener("click", () => {
        setMessage("");
        showPhoneStep();
    });

    document.getElementById("auth-phone-form").addEventListener("submit", (event) => {
        event.preventDefault();
        phone = document.getElementById("auth-phone").value.trim();
        if (!/^09\d{9}$/.test(phone)) {
            setMessage("شماره موبایل معتبر نیست (مثال: 09123456789)", true);
            return;
        }

        setMessage("در حال ارسال کد...");
        apiFetch("/otp/send", {
            method: "POST",
            body: JSON.stringify({ phone, purpose: mode }),
        }).then(({ ok, status, data }) => {
            if (!ok) {
                if (status === 429) {
                    setMessage(
                        data.detail || "تعداد درخواست زیاد است. کمی صبر کنید و دوباره تلاش کنید.",
                        true
                    );
                    return;
                }
                if (mode === "login" && (data.detail || "").includes("یافت نشد")) {
                    setMessage("کاربری با این شماره نیست. ثبت‌نام کنید.", true);
                    return;
                }
                if (mode === "register" && (data.detail || "").includes("ثبت شده")) {
                    setMessage("این شماره قبلاً ثبت شده. وارد شوید.", true);
                    return;
                }
                setMessage(data.detail || "خطا در ارسال کد", true);
                return;
            }
            expiresIn = data.expires_in || 120;
            setMessage("کد تأیید ارسال شد.");
            showVerifyStep();
        });
    });

    document.getElementById("auth-verify-form").addEventListener("submit", (event) => {
        event.preventDefault();
        const code = document.getElementById("auth-code").value.trim();
        if (!/^\d{5}$/.test(code)) {
            setMessage("کد ۵ رقمی را وارد کنید.", true);
            return;
        }

        const path = mode === "register" ? "/otp/verify/register" : "/otp/verify/login";
        const payload = { phone, code };
        if (mode === "register") {
            payload.first_name = document.getElementById("auth-first-name").value.trim();
            payload.last_name = document.getElementById("auth-last-name").value.trim();
        }

        setMessage("در حال تأیید...");
        apiFetch(path, {
            method: "POST",
            body: JSON.stringify(payload),
        }).then(({ ok, data }) => {
            if (!ok) {
                setMessage(data.detail || "کد نامعتبر است", true);
                return;
            }
            if (data.access_token) {
                sessionStorage.setItem("access_token", data.access_token);
            }
            if (data.refresh_token) {
                sessionStorage.setItem("refresh_token", data.refresh_token);
            }
            setMessage("ورود موفق. در حال انتقال...");
            window.location.href = getRedirectUrl(data);
        });
    });

    setMode(mode);
})();
