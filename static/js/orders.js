(function () {
    const API = "/api/v1/orders";

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
        }).then(async (res) => ({ ok: res.ok, status: res.status, data: await res.json() }));
    }

    function formatPrice(value) {
        if (window.ShopMoney) return window.ShopMoney.formatMoney(value, "IRR");
        return Number(value || 0).toLocaleString("fa-IR") + " تومان";
    }

    function formatAmount(value) {
        if (window.ShopMoney) return window.ShopMoney.formatAmount(value);
        return Number(value || 0).toLocaleString("fa-IR");
    }

    function formatDate(iso, withTime) {
        if (!iso) return "";
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return "";
        if (withTime) return d.toLocaleString("fa-IR");
        return d.toLocaleDateString("fa-IR", {
            year: "numeric",
            month: "long",
            day: "numeric",
        });
    }

    function escapeHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function statusBadgeClass(status) {
        switch (status) {
            case "delivered":
            case "paid":
                return "status-badge success";
            case "canceled":
            case "refunded":
                return "status-badge danger";
            case "waiting_payment":
            case "pending":
                return "status-badge warning";
            case "preparing":
            case "sent":
                return "status-badge";
            default:
                return "status-badge muted";
        }
    }

    function refreshIcons() {
        if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons({
                attrs: { "stroke-width": 1.75 },
                nameAttr: "data-lucide",
            });
        }
    }

    function renderOrderCard(order) {
        const number = escapeHtml(order.order_number);
        const label = escapeHtml(order.status_label || "");
        const date = escapeHtml(formatDate(order.created_at));
        const method = escapeHtml(order.shipping_method || "");
        return `
            <article class="ns-panel order-card">
                <div class="order-card-head">
                    <div class="order-card-id">
                        <h3 class="order-card-title">سفارش ${number}</h3>
                        <time class="order-card-date muted" datetime="${escapeHtml(order.created_at || "")}">${date}</time>
                    </div>
                    <span class="${statusBadgeClass(order.status)}">${label}</span>
                </div>
                <div class="order-card-stats" role="list">
                    <div class="order-card-stat" role="listitem">
                        <span class="order-card-stat-label">مبلغ کل</span>
                        <strong class="order-card-stat-value">${formatPrice(order.total)}</strong>
                    </div>
                    <div class="order-card-stat" role="listitem">
                        <span class="order-card-stat-label">اقلام</span>
                        <strong class="order-card-stat-value">${formatAmount(order.item_count)} قلم</strong>
                    </div>
                    ${method ? `<div class="order-card-stat" role="listitem">
                        <span class="order-card-stat-label">ارسال</span>
                        <strong class="order-card-stat-value">${method}</strong>
                    </div>` : ""}
                </div>
                <div class="order-card-actions">
                    <a href="/orders/${order.id}/" class="ns-btn ns-btn--ghost order-card-link">
                        جزئیات سفارش
                        <i data-lucide="chevron-left" aria-hidden="true"></i>
                    </a>
                </div>
            </article>
        `;
    }

    function renderOrderDetail(order) {
        const address = order.address || {};
        const shipment = order.shipment || {};
        const payment = order.payment || {};
        const items = order.items || [];
        const history = order.history || [];

        const itemsHtml = items.map((item) => `
            <li class="order-item">
                ${item.image
                    ? `<img class="order-item-thumb" src="${escapeHtml(item.image)}" alt="" loading="lazy" width="64" height="64">`
                    : `<span class="order-item-thumb order-item-thumb--empty" aria-hidden="true"><i data-lucide="package"></i></span>`}
                <div class="order-item-body">
                    <strong class="order-item-name">${escapeHtml(item.product_name)}</strong>
                    ${item.variant_label ? `<p class="ns-variant-chip">${escapeHtml(item.variant_label)}</p>` : ""}
                    <p class="order-item-qty muted">${formatAmount(item.quantity)} × ${formatPrice(item.unit_price)}</p>
                </div>
                <div class="order-item-total">${formatPrice(item.line_total)}</div>
            </li>
        `).join("");

        const historyHtml = history.map((h, index) => `
            <li class="history-item${index === 0 ? " is-current" : ""}">
                <span class="history-dot" aria-hidden="true"></span>
                <div class="history-body">
                    <strong>${escapeHtml(h.status)}</strong>
                    ${h.note ? `<p class="muted">${escapeHtml(h.note)}</p>` : ""}
                    <time class="muted" datetime="${escapeHtml(h.created_at || "")}">${escapeHtml(formatDate(h.created_at, true))}</time>
                </div>
            </li>
        `).join("");

        return `
            <section class="order-summary card" aria-labelledby="order-summary-title">
                <div class="order-summary-head">
                    <div>
                        <h2 id="order-summary-title" class="order-summary-title">${escapeHtml(order.order_number)}</h2>
                        <time class="muted" datetime="${escapeHtml(order.created_at || "")}">${escapeHtml(formatDate(order.created_at, true))}</time>
                    </div>
                    <span class="${statusBadgeClass(order.status)}">${escapeHtml(order.status_label || "")}</span>
                </div>
                <dl class="order-meta">
                    <div class="order-meta-item">
                        <dt>جمع اقلام</dt>
                        <dd>${formatPrice(order.subtotal)}</dd>
                    </div>
                    <div class="order-meta-item">
                        <dt>تخفیف</dt>
                        <dd>${formatPrice(order.discount)}</dd>
                    </div>
                    <div class="order-meta-item">
                        <dt>ارسال</dt>
                        <dd>${formatPrice(order.shipping_cost)}</dd>
                    </div>
                    <div class="order-meta-item order-meta-item--total">
                        <dt>مبلغ قابل پرداخت</dt>
                        <dd>${formatPrice(order.total)}</dd>
                    </div>
                </dl>
            </section>

            <div class="order-grid">
                <section class="card order-info-card" aria-labelledby="order-address-title">
                    <h3 id="order-address-title" class="order-section-title">
                        <i data-lucide="map-pin" aria-hidden="true"></i>
                        آدرس تحویل
                    </h3>
                    <p class="order-info-name">${escapeHtml(address.full_name || "—")}</p>
                    ${address.phone ? `<p class="muted order-info-phone">${escapeHtml(address.phone)}</p>` : ""}
                    <p class="order-info-address">${escapeHtml(address.full_address || address.address_line || "—")}</p>
                </section>
                <section class="card order-info-card" aria-labelledby="order-ship-title">
                    <h3 id="order-ship-title" class="order-section-title">
                        <i data-lucide="truck" aria-hidden="true"></i>
                        ارسال و پرداخت
                    </h3>
                    <p><span class="muted">روش ارسال:</span> ${escapeHtml(order.shipping_method || "—")}</p>
                    ${shipment.tracking_code
                        ? `<p><span class="muted">کد رهگیری:</span> <strong class="order-tracking">${escapeHtml(shipment.tracking_code)}</strong></p>`
                        : ""}
                    ${payment.tracking_code
                        ? `<p class="muted">پرداخت: ${escapeHtml(payment.tracking_code)}${payment.ref_id ? " — " + escapeHtml(payment.ref_id) : ""}</p>`
                        : ""}
                </section>
            </div>

            <section class="card order-items-card" aria-labelledby="order-items-title">
                <h3 id="order-items-title" class="order-section-title">
                    <i data-lucide="shopping-bag" aria-hidden="true"></i>
                    اقلام سفارش
                    <span class="order-section-count muted">${formatAmount(items.length)}</span>
                </h3>
                ${itemsHtml
                    ? `<ul class="order-items-list">${itemsHtml}</ul>`
                    : '<p class="muted">بدون آیتم</p>'}
            </section>

            ${historyHtml
                ? `<section class="card order-history-card" aria-labelledby="order-history-title">
                    <h3 id="order-history-title" class="order-section-title">
                        <i data-lucide="history" aria-hidden="true"></i>
                        تاریخچه وضعیت
                    </h3>
                    <ol class="history-list">${historyHtml}</ol>
                </section>`
                : ""}
        `;
    }

    const listRoot = document.getElementById("orders-page");
    if (listRoot) {
        apiFetch("/").then(({ ok, data }) => {
            const list = document.getElementById("orders-list");
            if (!list) return;
            if (!ok) {
                list.innerHTML =
                    '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="log-in"></i></div>' +
                    "<strong>ورود لازم است</strong><p>برای مشاهده سفارشات وارد حساب شوید.</p>" +
                    '<a href="/login/?next=/orders/" class="ns-btn">ورود</a></div>';
                refreshIcons();
                return;
            }
            if (!data.length) {
                list.innerHTML =
                    '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="package"></i></div>' +
                    "<strong>هنوز سفارشی ندارید</strong><p>اولین خریدتان را از فروشگاه شروع کنید.</p>" +
                    '<a href="/products/" class="ns-btn">شروع خرید</a></div>';
                refreshIcons();
                return;
            }
            list.classList.add("orders-list");
            list.innerHTML = data.map(renderOrderCard).join("");
            refreshIcons();
        });
    }

    const detailRoot = document.getElementById("order-detail-page");
    if (detailRoot) {
        const orderId = detailRoot.dataset.orderId;
        apiFetch(`/${orderId}`).then(({ ok, data }) => {
            const container = document.getElementById("order-detail-content");
            if (!container) return;
            if (!ok) {
                container.innerHTML =
                    '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="search-x"></i></div>' +
                    "<strong>سفارش یافت نشد</strong><p>ممکن است لینک منقضی شده باشد.</p>" +
                    '<a href="/orders/" class="ns-btn ns-btn--ghost">بازگشت به سفارشات</a></div>';
                refreshIcons();
                return;
            }
            container.classList.add("order-detail");
            container.innerHTML = renderOrderDetail(data);
            refreshIcons();
        });
    }
})();
