(function () {
    const root = document.getElementById("subscriptions-page");
    if (!root) return;

    const API = "/api/v1/subscriptions";

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
        }).then(async (res) => ({ ok: res.ok, status: res.status, data: await res.json().catch(() => ({})) }));
    }

    function formatDate(value) {
        if (!value) return "—";
        return new Date(value).toLocaleString("fa-IR");
    }

    function renderSub(item) {
        const canRenew = item.status === "past_due" || (item.status === "active" && !item.auto_renew);
        const canCancel = item.status === "active" || item.status === "trialing" || item.status === "past_due";
        return `
            <div class="card subscription-card" data-id="${item.id}">
                <div style="display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
                    <div>
                        <h3>${item.product_name}</h3>
                        <p class="muted">${item.interval_label} — ${window.ShopMoney ? window.ShopMoney.formatMoney(item.price, "IRR") : (Number(item.price).toLocaleString("en-US") + " تومان")}</p>
                    </div>
                    <span class="status-badge">${item.status_label}</span>
                </div>
                <p class="muted" style="margin:0.5rem 0;">
                    پایان دوره: ${formatDate(item.current_period_end)}
                    ${item.trial_ends_at ? ` — پایان آزمایشی: ${formatDate(item.trial_ends_at)}` : ""}
                </p>
                <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
                    ${canRenew ? `<button type="button" class="btn btn-outline renew-sub" data-id="${item.id}">تمدید</button>` : ""}
                    ${canCancel ? `<button type="button" class="btn btn-outline cancel-sub" data-id="${item.id}">لغو</button>` : ""}
                </div>
            </div>
        `;
    }

    function bindActions() {
        document.querySelectorAll(".renew-sub").forEach((btn) => {
            btn.addEventListener("click", () => {
                apiFetch(`/${btn.dataset.id}/renew`, { method: "POST", body: "{}" }).then(load);
            });
        });
        document.querySelectorAll(".cancel-sub").forEach((btn) => {
            btn.addEventListener("click", () => {
                if (!confirm("اشتراک در پایان دوره لغو شود؟")) return;
                apiFetch(`/${btn.dataset.id}/cancel`, {
                    method: "POST",
                    body: JSON.stringify({ immediate: false }),
                }).then(load);
            });
        });
    }

    function renderList(items) {
        const container = document.getElementById("subscriptions-container");
        if (!items.length) {
            container.innerHTML = '<div class="empty-state card">اشتراک فعالی ندارید.</div>';
            return;
        }
        container.innerHTML = items.map(renderSub).join("");
        bindActions();
    }

    function load() {
        apiFetch("/").then(({ ok, status, data }) => {
            const container = document.getElementById("subscriptions-container");
            if (status === 401) {
                container.innerHTML = '<div class="empty-state card">برای مشاهده اشتراک‌ها <a href="/login/?next=/subscriptions/">وارد شوید</a>.</div>';
                return;
            }
            if (!ok) {
                container.innerHTML = '<div class="empty-state card">خطا در بارگذاری.</div>';
                return;
            }
            renderList(data);
        });
    }

    load();
})();
