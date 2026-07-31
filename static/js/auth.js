(function () {
    const root = document.getElementById("auth-page");
    if (!root) return;

    const API = "/api/v1/auth";
    const unified = root.dataset.unified === "1";
    let mode = root.dataset.mode || "login";
    let phone = "";
    let expiresIn = 120;
    let countdownTimer = null;
    let pendingRedirect = "/dashboard/";
    let isNewRegistration = false;

    // Capture ?next= immediately so unified OTP + name steps keep return URL.
    (function captureNextEarly() {
        const params = new URLSearchParams(window.location.search);
        const next = params.get("next");
        if (next && next.startsWith("/") && !next.startsWith("//")) {
            pendingRedirect = next;
        }
    })();

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
        const token = sessionStorage.getItem("access_token");
        if (token && !headers.Authorization) {
            headers.Authorization = "Bearer " + token;
        }
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
            const active = btn.dataset.mode === mode;
            btn.classList.toggle("is-active", active);
            btn.classList.toggle("btn", active);
            btn.classList.toggle("btn-outline", !active);
            btn.classList.toggle("ps-btn--ghost", !active);
            btn.setAttribute("aria-selected", active ? "true" : "false");
        });
        const registerFields = document.getElementById("register-fields");
        if (registerFields && !unified) {
            registerFields.style.display = mode === "register" ? "grid" : "none";
        }
        const title = mode === "register" ? "ثبت‌نام" : mode === "auth" ? "ورود / عضویت" : "ورود";
        const titleEl = root.querySelector(".ns-page-title, .page-title, .ps-auth-title, .ps-page-title");
        if (titleEl && !unified) titleEl.textContent = title;
        if (!unified) {
            document.title = document.title.replace(/(ورود \/ عضویت|ورود|ثبت‌نام)/, title);
        }
    }

    function showVerifyStep() {
        document.getElementById("auth-phone-form").style.display = "none";
        document.getElementById("auth-verify-form").style.display = "grid";
        const nameForm = document.getElementById("auth-name-form");
        if (nameForm) nameForm.style.display = "none";
        document.getElementById("auth-phone-display").textContent = `کد به ${phone} ارسال شد.`;
        document.getElementById("auth-code").focus();
        startCountdown();
    }

    function showPhoneStep() {
        document.getElementById("auth-phone-form").style.display = "grid";
        document.getElementById("auth-verify-form").style.display = "none";
        const nameForm = document.getElementById("auth-name-form");
        if (nameForm) nameForm.style.display = "none";
        if (countdownTimer) clearInterval(countdownTimer);
        const btn = document.getElementById("auth-send-btn");
        btn.disabled = false;
        setSendButtonLabel(unified ? "ادامه" : "دریافت کد");
    }

    function showNameStep() {
        document.getElementById("auth-phone-form").style.display = "none";
        document.getElementById("auth-verify-form").style.display = "none";
        const nameForm = document.getElementById("auth-name-form");
        if (!nameForm) {
            finishRedirect();
            return;
        }
        nameForm.style.display = "grid";
        const lead = document.getElementById("auth-lead");
        if (lead) lead.textContent = "برای تکمیل پروفایل نام خود را وارد کنید";
        const titleEl = root.querySelector(".ps-auth-title, .ps-page-title");
        if (titleEl) titleEl.textContent = "نام شما";
        document.getElementById("auth-first-name")?.focus();
    }

    function setSendButtonLabel(label) {
        const btn = document.getElementById("auth-send-btn");
        if (!btn) return;
        btn.innerHTML = label;
        if (window.lucide) window.lucide.createIcons();
    }

    function startCountdown() {
        let remaining = expiresIn;
        const btn = document.getElementById("auth-send-btn");
        btn.disabled = true;
        setSendButtonLabel("ارسال مجدد (" + remaining + ")");
        if (countdownTimer) clearInterval(countdownTimer);
        countdownTimer = setInterval(() => {
            remaining -= 1;
            if (remaining <= 0) {
                clearInterval(countdownTimer);
                btn.disabled = false;
                setSendButtonLabel("ارسال مجدد کد");
                showPhoneStep();
                return;
            }
            setSendButtonLabel("ارسال مجدد (" + remaining + ")");
        }, 1000);
    }

    function getRedirectUrl(loginData) {
        const params = new URLSearchParams(window.location.search);
        const next = params.get("next");
        if (next && next.startsWith("/") && !next.startsWith("//")) return next;
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

    function storeTokens(data) {
        if (data.access_token) sessionStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) sessionStorage.setItem("refresh_token", data.refresh_token);
    }

    function finishRedirect() {
        setMessage("ورود موفق. در حال انتقال...");
        window.location.href = pendingRedirect;
    }

    function needsNamePrompt(user) {
        if (!user) return false;
        const first = (user.first_name || "").trim();
        const last = (user.last_name || "").trim();
        return !first && !last;
    }

    function handleAuthSuccess(data) {
        storeTokens(data);
        pendingRedirect = getRedirectUrl(data);
        if (unified && isNewRegistration && needsNamePrompt(data.user)) {
            setMessage("");
            showNameStep();
            return;
        }
        finishRedirect();
    }

    function normalizePurpose(purpose) {
        if (purpose === "login" || purpose === "register") return purpose;
        return null;
    }

    function sendOtp(purpose) {
        // Prefer login|register; "auth" is the unified-storefront alias the API resolves.
        const resolved = normalizePurpose(purpose) || (purpose === "auth" ? "auth" : null);
        if (!resolved) {
            setMessage("خطا در تشخیص نوع ورود. دوباره تلاش کنید.", true);
            return Promise.resolve(false);
        }
        setMessage("در حال ارسال کد...");
        return apiFetch("/otp/send", {
            method: "POST",
            body: JSON.stringify({ phone, purpose: resolved }),
        }).then(({ ok, status, data }) => {
            if (!ok) {
                if (status === 429) {
                    setMessage(
                        data.detail || "تعداد درخواست زیاد است. کمی صبر کنید و دوباره تلاش کنید.",
                        true
                    );
                    return false;
                }
                if (resolved === "login" && (data.detail || "").includes("یافت نشد")) {
                    setMessage("کاربری با این شماره نیست. ثبت‌نام کنید.", true);
                    return false;
                }
                if (resolved === "register" && (data.detail || "").includes("ثبت شده")) {
                    setMessage("این شماره قبلاً ثبت شده. وارد شوید.", true);
                    return false;
                }
                setMessage(data.detail || "خطا در ارسال کد", true);
                return false;
            }
            mode = normalizePurpose(data.purpose) || normalizePurpose(resolved) || "login";
            isNewRegistration = mode === "register";
            expiresIn = data.expires_in || 120;
            setMessage("کد تأیید ارسال شد.");
            showVerifyStep();
            return true;
        });
    }

    document.querySelectorAll(".auth-tab").forEach((btn) => {
        btn.addEventListener("click", () => {
            setMode(btn.dataset.mode);
            setMessage("");
            showPhoneStep();
        });
    });

    document.getElementById("auth-back-btn")?.addEventListener("click", () => {
        setMessage("");
        showPhoneStep();
    });

    document.getElementById("auth-skip-name-btn")?.addEventListener("click", () => {
        finishRedirect();
    });

    document.getElementById("auth-name-form")?.addEventListener("submit", (event) => {
        event.preventDefault();
        const first_name = document.getElementById("auth-first-name").value.trim();
        const last_name = document.getElementById("auth-last-name").value.trim();
        if (!first_name && !last_name) {
            finishRedirect();
            return;
        }
        setMessage("در حال ذخیره...");
        apiFetch("/me", {
            method: "PATCH",
            body: JSON.stringify({ first_name, last_name }),
        }).then(({ ok, data }) => {
            if (!ok) {
                setMessage(data.detail || "ذخیره نام ناموفق بود", true);
                return;
            }
            finishRedirect();
        });
    });

    document.getElementById("auth-phone-form").addEventListener("submit", (event) => {
        event.preventDefault();
        phone = document.getElementById("auth-phone").value.trim();
        if (!/^09\d{9}$/.test(phone)) {
            setMessage("شماره موبایل معتبر نیست (مثال: 09123456789)", true);
            return;
        }

        if (unified) {
            setMessage("در حال بررسی شماره...");
            apiFetch("/phone/lookup", {
                method: "POST",
                body: JSON.stringify({ phone }),
            }).then(({ ok, data }) => {
                if (!ok) {
                    // Backend still resolves purpose="auth" from phone existence
                    sendOtp("auth");
                    return;
                }
                const purpose =
                    normalizePurpose(data.purpose) ||
                    (data.exists ? "login" : "register");
                setMode(purpose);
                sendOtp(purpose);
            });
            return;
        }

        sendOtp(normalizePurpose(mode) || "login");
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
        if (mode === "register" && !unified) {
            payload.first_name = document.getElementById("auth-first-name")?.value.trim() || "";
            payload.last_name = document.getElementById("auth-last-name")?.value.trim() || "";
        }

        setMessage("در حال تأیید...");
        apiFetch(path, {
            method: "POST",
            body: JSON.stringify(payload),
        }).then(({ ok, status, data }) => {
            if (!ok) {
                setMessage(data.detail || "کد نامعتبر است", true);
                return;
            }
            if (status === 202 || data.requires_2fa) {
                setMessage("این حساب نیاز به تأیید دومرحله‌ای دارد. از پنل مدیریت وارد شوید.", true);
                return;
            }
            isNewRegistration = mode === "register";
            handleAuthSuccess(data);
        });
    });

    // Never leave mode as "auth" — that value is not a valid OTP purpose.
    if (unified) {
        setMode(normalizePurpose(mode) || "login");
        showPhoneStep();
    } else {
        setMode(normalizePurpose(mode) || "login");
    }
})();
