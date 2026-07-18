(function () {
    const API = "/api/v1/cart";

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
        }).then((res) => res.json().then((data) => ({ ok: res.ok, status: res.status, data })));
    }

    function formatMoney(value, currency) {
        if (window.ShopMoney) return window.ShopMoney.formatMoney(value, currency);
        return Number(value || 0).toLocaleString("en-US") + (currency ? " " + currency : "");
    }

    function updateCartBadge(count) {
        document.querySelectorAll("[data-cart-count]").forEach((el) => {
            el.textContent = count;
            el.style.display = count > 0 ? "inline-block" : "none";
        });
    }

    function renderCartItem(item, currency) {
        return `
            <div class="cart-item card" data-item-id="${item.id}">
                <div class="cart-item-info">
                    ${item.image ? `<img src="${item.image}" alt="${item.product_name}" class="cart-item-img">` : ""}
                    <div>
                        <h3>${item.product_name}</h3>
                        ${item.variant_label ? `<p class="muted">${item.variant_label}</p>` : ""}
                        <p class="cart-item-price">${formatMoney(item.unit_price, currency)}</p>
                    </div>
                </div>
                <div class="cart-item-actions">
                    <div class="qty-control">
                        <button type="button" class="btn btn-outline qty-minus" data-id="${item.id}">−</button>
                        <span class="qty-value">${item.quantity}</span>
                        <button type="button" class="btn btn-outline qty-plus" data-id="${item.id}">+</button>
                    </div>
                    <p class="line-total">${formatMoney(item.line_total, currency)}</p>
                    <button type="button" class="btn btn-outline remove-item" data-id="${item.id}">حذف</button>
                </div>
            </div>
        `;
    }

    function renderCart(cart, currency) {
        const container = document.getElementById("cart-container");
        const summary = document.getElementById("cart-summary");
        if (!container) return;

        updateCartBadge(cart.item_count || 0);

        if (!cart.items || !cart.items.length) {
            container.innerHTML = '<div class="empty-state card">سبد خرید شما خالی است.</div>';
            if (summary) summary.innerHTML = "";
            return;
        }

        container.innerHTML = cart.items.map((item) => renderCartItem(item, currency)).join("");

        if (summary) {
            summary.innerHTML = `
                <div class="card">
                    <p>جمع کل: <strong>${formatMoney(cart.subtotal, currency)}</strong></p>
                    ${cart.discount && cart.discount !== "0" ? `<p>تخفیف: <strong>${formatMoney(cart.discount, currency)}</strong></p>` : ""}
                    ${cart.coupon ? `<p class="muted">کوپن: ${cart.coupon.code}</p>` : ""}
                    ${cart.gift_card ? `<p class="muted">کارت هدیه: ${cart.gift_card.code}</p>` : ""}
                    <p style="font-size:1.2rem; margin-top:0.5rem;">مبلغ قابل پرداخت: <strong style="color:var(--accent);">${formatMoney(cart.total, currency)}</strong></p>
                    <a href="/checkout/" class="btn" style="margin-top:1rem; display:inline-block;">تسویه حساب</a>
                </div>
            `;
        }

        container.querySelectorAll(".qty-minus").forEach((btn) => {
            btn.addEventListener("click", () => {
                const id = Number(btn.dataset.id);
                const item = cart.items.find((i) => i.id === id);
                if (item) updateQuantity(id, item.quantity - 1);
            });
        });
        container.querySelectorAll(".qty-plus").forEach((btn) => {
            btn.addEventListener("click", () => {
                const id = Number(btn.dataset.id);
                const item = cart.items.find((i) => i.id === id);
                if (item) updateQuantity(id, item.quantity + 1);
            });
        });
        container.querySelectorAll(".remove-item").forEach((btn) => {
            btn.addEventListener("click", () => removeItem(Number(btn.dataset.id)));
        });
    }

    function updateQuantity(itemId, quantity) {
        apiFetch("/update", {
            method: "POST",
            body: JSON.stringify({ item_id: itemId, quantity }),
        }).then(({ ok, data }) => {
            if (ok) renderCart(data, getCurrency());
        });
    }

    function removeItem(itemId) {
        apiFetch("/remove", {
            method: "POST",
            body: JSON.stringify({ item_id: itemId }),
        }).then(({ ok, data }) => {
            if (ok) renderCart(data, getCurrency());
        });
    }

    function getCurrency() {
        const root = document.getElementById("cart-page") || document.body;
        return root.dataset.currency || "";
    }

    function loadCart() {
        apiFetch("/").then(({ ok, data }) => {
            if (ok) renderCart(data, getCurrency());
        });
    }

    function applyCoupon() {
        const input = document.getElementById("coupon-code");
        if (!input || !input.value.trim()) return;
        apiFetch("/coupon/apply", {
            method: "POST",
            body: JSON.stringify({ code: input.value.trim() }),
        }).then(({ ok, data }) => {
            const msg = document.getElementById("coupon-message");
            if (ok) {
                if (msg) msg.textContent = "کوپن اعمال شد";
                renderCart(data, getCurrency());
            } else if (msg) {
                msg.textContent = data.detail || "کوپن نامعتبر است";
            }
        });
    }

    function removeCoupon() {
        apiFetch("/coupon/remove", { method: "POST", body: "{}" }).then(({ ok, data }) => {
            if (ok) {
                const msg = document.getElementById("coupon-message");
                if (msg) msg.textContent = "";
                renderCart(data, getCurrency());
            }
        });
    }

    function applyGiftCard() {
        const input = document.getElementById("gift-code");
        if (!input || !input.value.trim()) return;
        apiFetch("/gift-card/apply", {
            method: "POST",
            body: JSON.stringify({ code: input.value.trim() }),
        }).then(({ ok, data }) => {
            const msg = document.getElementById("coupon-message");
            if (ok) {
                if (msg) msg.textContent = "کارت هدیه اعمال شد";
                renderCart(data, getCurrency());
            } else if (msg) {
                msg.textContent = data.detail || "کارت هدیه نامعتبر است";
            }
        });
    }

    function removeGiftCard() {
        apiFetch("/gift-card/remove", { method: "POST", body: "{}" }).then(({ ok, data }) => {
            if (ok) {
                const msg = document.getElementById("coupon-message");
                if (msg) msg.textContent = "";
                renderCart(data, getCurrency());
            }
        });
    }

    function addToCart(productSlug, variantId, quantity) {
        return apiFetch("/add", {
            method: "POST",
            body: JSON.stringify({
                product_slug: productSlug,
                variant_id: variantId || null,
                quantity: quantity || 1,
            }),
        }).then(({ ok, data }) => {
            if (ok) {
                updateCartBadge(data.item_count || 0);
                return { ok: true, cart: data };
            }
            return { ok: false, error: data.detail || "خطا" };
        });
    }

    document.querySelectorAll("[data-add-to-cart]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const slug = btn.dataset.product;
            const variantId = btn.dataset.variant ? Number(btn.dataset.variant) : null;
            btn.disabled = true;
            addToCart(slug, variantId, 1).then((result) => {
                btn.disabled = false;
                if (result.ok) {
                    const original = btn.textContent;
                    btn.textContent = "اضافه شد ✓";
                    setTimeout(() => { btn.textContent = original; }, 1500);
                } else {
                    alert(result.error);
                }
            });
        });
    });

    document.getElementById("apply-coupon")?.addEventListener("click", applyCoupon);
    document.getElementById("remove-coupon")?.addEventListener("click", removeCoupon);
    document.getElementById("apply-gift")?.addEventListener("click", applyGiftCard);
    document.getElementById("remove-gift")?.addEventListener("click", removeGiftCard);

    if (document.getElementById("cart-page")) {
        loadCart();
    } else {
        apiFetch("/count").then(({ ok, data }) => {
            if (ok) updateCartBadge(data.item_count || 0);
        });
    }

    window.ShopCart = { addToCart, loadCart, updateCartBadge };
})();
