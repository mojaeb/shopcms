(function () {
    const root = document.getElementById("downloads-page");
    if (!root) return;

    const API = "/api/v1/downloads";

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : "";
    }

    function apiFetch(path, options = {}) {
        const headers = {
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

    function statusClass(status) {
        if (status === "active") return "status-badge success";
        return "status-badge";
    }

    function renderLicense(item) {
        const canDownload = item.status === "active" && item.downloads_remaining > 0;
        return `
            <div class="card download-card" data-token="${item.token}">
                <div style="display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
                    <div>
                        <h3>${item.file_title}</h3>
                        <p class="muted">${item.product_name} — سفارش ${item.order_number}</p>
                    </div>
                    <span class="${statusClass(item.status)}">${item.status_label}</span>
                </div>
                <p class="muted" style="margin:0.5rem 0;">
                    باقیمانده: ${item.downloads_remaining} از ${item.max_downloads}
                    ${item.expires_at ? ` — انقضا: ${formatDate(item.expires_at)}` : ""}
                </p>
                ${
                    canDownload
                        ? `<a href="${item.download_url}" class="btn" download>دانلود</a>`
                        : `<button type="button" class="btn btn-outline" disabled>غیرفعال</button>`
                }
            </div>
        `;
    }

    function renderList(items) {
        const container = document.getElementById("downloads-container");
        if (!items.length) {
            container.innerHTML = '<div class="empty-state card">دانلودی موجود نیست.</div>';
            return;
        }
        container.innerHTML = items.map(renderLicense).join("");
    }

    apiFetch("/").then(({ ok, status, data }) => {
        const container = document.getElementById("downloads-container");
        if (status === 401) {
            container.innerHTML = '<div class="empty-state card">برای مشاهده دانلودها <a href="/login/?next=/downloads/">وارد شوید</a>.</div>';
            return;
        }
        if (!ok) {
            container.innerHTML = '<div class="empty-state card">خطا در بارگذاری دانلودها.</div>';
            return;
        }
        renderList(data);
    });
})();
