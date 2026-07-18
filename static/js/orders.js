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
        return Number(value || 0).toLocaleString("en-US") + " تومان";
    }

    function formatDate(iso) {
        if (!iso) return "";
        return new Date(iso).toLocaleString("fa-IR");
    }

    function renderOrderCard(order) {
        return `
            <div class="card order-card">
                <div style="display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
                    <div>
                        <h3>سفارش ${order.order_number}</h3>
                        <p class="muted">${formatDate(order.created_at)}</p>
                        <span class="status-badge">${order.status_label}</span>
                    </div>
                    <div style="text-align:left;">
                        <p><strong>${formatPrice(order.total)}</strong></p>
                        <p class="muted">${order.item_count} قلم</p>
                        <a href="/orders/${order.id}/" class="btn btn-outline">جزئیات</a>
                    </div>
                </div>
            </div>
        `;
    }

    function renderOrderDetail(order) {
        const address = order.address || {};
        const itemsHtml = (order.items || []).map((item) => `
            <div class="order-item">
                ${item.image ? `<img src="${item.image}" alt="">` : ""}
                <div>
                    <strong>${item.product_name}</strong>
                    ${item.variant_label ? `<p class="muted">${item.variant_label}</p>` : ""}
                    <p class="muted">${item.quantity} × ${formatPrice(item.unit_price)}</p>
                </div>
                <div style="margin-right:auto;">${formatPrice(item.line_total)}</div>
            </div>
        `).join("");

        const historyHtml = (order.history || []).map((h) => `
            <div class="history-item">
                <strong>${h.status}</strong>
                <p class="muted">${h.note}</p>
                <p class="muted">${formatDate(h.created_at)}</p>
            </div>
        `).join("");

        const shipment = order.shipment || {};
        const payment = order.payment || {};

        return `
            <div class="card">
                <h2>${order.order_number}</h2>
                <p class="muted">${formatDate(order.created_at)} — ${order.status_label}</p>
                <div class="order-meta">
                    <span>جمع: ${formatPrice(order.subtotal)}</span>
                    <span>تخفیف: ${formatPrice(order.discount)}</span>
                    <span>ارسال: ${formatPrice(order.shipping_cost)}</span>
                    <span><strong>کل: ${formatPrice(order.total)}</strong></span>
                </div>
            </div>
            <div class="order-grid">
                <div class="card">
                    <h3>آدرس تحویل</h3>
                    <p>${address.full_name || ""}</p>
                    <p class="muted">${address.phone || ""}</p>
                    <p>${address.full_address || address.address_line || ""}</p>
                </div>
                <div class="card">
                    <h3>ارسال و پرداخت</h3>
                    <p>روش ارسال: ${order.shipping_method || "-"}</p>
                    ${shipment.tracking_code ? `<p>کد رهگیری: ${shipment.tracking_code}</p>` : ""}
                    ${payment.tracking_code ? `<p class="muted">پرداخت: ${payment.tracking_code}${payment.ref_id ? " — " + payment.ref_id : ""}</p>` : ""}
                </div>
            </div>
            <div class="card" style="margin-top:1rem;">
                <h3>اقلام سفارش</h3>
                ${itemsHtml || '<p class="muted">بدون آیتم</p>'}
            </div>
            ${historyHtml ? `<div class="card" style="margin-top:1rem;"><h3>تاریخچه</h3>${historyHtml}</div>` : ""}
        `;
    }

    const listRoot = document.getElementById("orders-page");
    if (listRoot) {
        apiFetch("/").then(({ ok, data }) => {
            const list = document.getElementById("orders-list");
            if (!list) return;
            if (!ok) {
                list.innerHTML = '<div class="empty-state card">برای مشاهده سفارشات وارد شوید.</div>';
                return;
            }
            if (!data.length) {
                list.innerHTML = '<div class="empty-state card">سفارشی ثبت نشده است.</div>';
                return;
            }
            list.innerHTML = data.map(renderOrderCard).join("");
        });
    }

    const detailRoot = document.getElementById("order-detail-page");
    if (detailRoot) {
        const orderId = detailRoot.dataset.orderId;
        apiFetch(`/${orderId}`).then(({ ok, data }) => {
            const container = document.getElementById("order-detail-content");
            if (!container) return;
            if (!ok) {
                container.innerHTML = '<div class="empty-state card">سفارش یافت نشد.</div>';
                return;
            }
            container.innerHTML = renderOrderDetail(data);
        });
    }
})();
