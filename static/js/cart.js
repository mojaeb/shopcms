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
        const access = sessionStorage.getItem("access_token");
        if (access) headers.Authorization = "Bearer " + access;

        return fetch(API + path, {
            credentials: "same-origin",
            ...options,
            headers,
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

    function requireLogin() {
        const next = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = "/login/?next=" + next;
    }

    function isLoggedIn() {
        return (
            document.body.dataset.authenticated === "1" ||
            Boolean(sessionStorage.getItem("access_token"))
        );
    }

    function isPolishedTheme() {
        return (
            document.body.classList.contains("theme-pulse") ||
            document.body.classList.contains("theme-nextshop")
        );
    }

    function escapeHtml(str) {
        return String(str ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function refreshIcons() {
        if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons();
        }
    }

    function formatMoney(value, currency) {
        if (window.ShopMoney) return window.ShopMoney.formatMoney(value, currency);
        return Number(value || 0).toLocaleString("fa-IR") + (currency ? " " + currency : "");
    }

    function updateCartBadge(count) {
        const n = Number(count) || 0;
        const label = window.ShopMoney ? window.ShopMoney.formatAmount(n) : String(n);
        document.querySelectorAll("[data-cart-count]").forEach((el) => {
            el.textContent = label;
            el.style.display = n > 0 ? "inline-block" : "none";
        });
    }

    function formatQty(value) {
        if (window.ShopMoney) return window.ShopMoney.formatAmount(value);
        return String(value ?? 0);
    }

    function setCartChrome(hasItems) {
        const layout = document.querySelector(".ps-cart-layout");
        if (layout) layout.classList.toggle("is-empty", !hasItems);
        document.querySelectorAll("[data-ps-cart-tools]").forEach((el) => {
            el.hidden = !hasItems;
        });
    }

    function renderCartItem(item, currency) {
        if (isPolishedTheme()) {
            const name = escapeHtml(item.product_name);
            const img = item.image
                ? `<img src="${escapeHtml(item.image)}" alt="${name}" class="cart-item-img" loading="lazy" width="88" height="88">`
                : `<div class="cart-item-img cart-item-img--empty" aria-hidden="true"><i data-lucide="image-off"></i></div>`;
            const variant = item.variant_label
                ? `<p class="ns-variant-chip"><i data-lucide="layers" aria-hidden="true"></i><span>${escapeHtml(item.variant_label)}</span></p>`
                : "";
            return `
            <div class="cart-item card ps-cart-item" data-item-id="${item.id}">
                <div class="cart-item-info">
                    ${img}
                    <div class="ps-cart-item-body">
                        <h3 class="ps-cart-item-title">${name}</h3>
                        ${variant}
                        <p class="cart-item-price">${formatMoney(item.unit_price, currency)}</p>
                    </div>
                </div>
                <div class="cart-item-actions">
                    <div class="qty-control" role="group" aria-label="تعداد">
                        <button type="button" class="btn btn-outline qty-minus" data-id="${item.id}" aria-label="کاهش تعداد">
                            <i data-lucide="minus" aria-hidden="true"></i>
                        </button>
                        <span class="qty-value">${formatQty(item.quantity)}</span>
                        <button type="button" class="btn btn-outline qty-plus" data-id="${item.id}" aria-label="افزایش تعداد">
                            <i data-lucide="plus" aria-hidden="true"></i>
                        </button>
                    </div>
                    <p class="line-total">${formatMoney(item.line_total, currency)}</p>
                    <button type="button" class="btn btn-outline remove-item" data-id="${item.id}" aria-label="حذف از سبد">
                        <i data-lucide="trash-2" aria-hidden="true"></i>
                        <span>حذف</span>
                    </button>
                </div>
            </div>`;
        }

        return `
            <div class="cart-item card" data-item-id="${item.id}">
                <div class="cart-item-info">
                    ${item.image ? `<img src="${item.image}" alt="${item.product_name}" class="cart-item-img">` : ""}
                    <div>
                        <h3>${item.product_name}</h3>
                        ${item.variant_label ? `<p class="ns-variant-chip"><i data-lucide="layers" aria-hidden="true"></i>${item.variant_label}</p>` : ""}
                        <p class="cart-item-price">${formatMoney(item.unit_price, currency)}</p>
                    </div>
                </div>
                <div class="cart-item-actions">
                    <div class="qty-control">
                        <button type="button" class="btn btn-outline qty-minus" data-id="${item.id}">−</button>
                        <span class="qty-value">${formatQty(item.quantity)}</span>
                        <button type="button" class="btn btn-outline qty-plus" data-id="${item.id}">+</button>
                    </div>
                    <p class="line-total">${formatMoney(item.line_total, currency)}</p>
                    <button type="button" class="btn btn-outline remove-item" data-id="${item.id}">حذف</button>
                </div>
            </div>
        `;
    }

    function renderSummary(cart, currency) {
        const summary = document.getElementById("cart-summary");
        if (!summary) return;

        if (isPolishedTheme()) {
            summary.innerHTML = `
                <div class="card ps-cart-summary-card">
                    <h2 class="ps-cart-summary-title">
                        <i data-lucide="receipt" aria-hidden="true"></i>
                        خلاصه سبد
                    </h2>
                    <div class="ps-cart-summary-rows">
                        <p><span>جمع کل</span><strong>${formatMoney(cart.subtotal, currency)}</strong></p>
                        ${
                            cart.discount && cart.discount !== "0"
                                ? `<p><span>تخفیف</span><strong>${formatMoney(cart.discount, currency)}</strong></p>`
                                : ""
                        }
                        ${cart.coupon ? `<p class="muted"><span>کوپن</span><strong>${escapeHtml(cart.coupon.code)}</strong></p>` : ""}
                        ${cart.gift_card ? `<p class="muted"><span>کارت هدیه</span><strong>${escapeHtml(cart.gift_card.code)}</strong></p>` : ""}
                        <p class="ps-cart-summary-total">
                            <span>مبلغ قابل پرداخت</span>
                            <strong>${formatMoney(cart.total, currency)}</strong>
                        </p>
                    </div>
                    <div class="ps-cart-summary-actions">
                        <a href="/checkout/" class="ns-btn">تسویه حساب</a>
                        <a href="/products/" class="ns-btn ns-btn--ghost">ادامه خرید</a>
                    </div>
                </div>`;
            return;
        }

        summary.innerHTML = `
                <div class="card">
                    <p>جمع کل: <strong>${formatMoney(cart.subtotal, currency)}</strong></p>
                    ${cart.discount && cart.discount !== "0" ? `<p>تخفیف: <strong>${formatMoney(cart.discount, currency)}</strong></p>` : ""}
                    ${cart.coupon ? `<p class="muted">کوپن: ${cart.coupon.code}</p>` : ""}
                    ${cart.gift_card ? `<p class="muted">کارت هدیه: ${cart.gift_card.code}</p>` : ""}
                    <p style="font-size:1.2rem; margin-top:0.5rem;">مبلغ قابل پرداخت: <strong style="color:var(--accent);">${formatMoney(cart.total, currency)}</strong></p>
                    <a href="/checkout/" class="ns-btn" style="margin-top:1rem; display:inline-flex;">تسویه حساب</a>
                </div>
            `;
    }

    function bindCartItemActions(container, cart) {
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

    function renderCart(cart, currency) {
        const container = document.getElementById("cart-container");
        const summary = document.getElementById("cart-summary");
        if (!container) return;

        updateCartBadge(cart.item_count || 0);

        if (!cart.items || !cart.items.length) {
            setCartChrome(false);
            container.innerHTML =
                '<div class="ns-empty">' +
                '<div class="ns-empty-icon" aria-hidden="true"><i data-lucide="shopping-cart"></i></div>' +
                "<strong>سبد خرید خالی است</strong>" +
                "<p>محصولی اضافه نشده. از فروشگاه انتخاب کنید و برگردید.</p>" +
                '<a href="/products/" class="ns-btn">مشاهده محصولات</a>' +
                "</div>";
            refreshIcons();
            if (summary) summary.innerHTML = "";
            return;
        }

        setCartChrome(true);
        container.innerHTML = cart.items.map((item) => renderCartItem(item, currency)).join("");
        renderSummary(cart, currency);
        refreshIcons();
        bindCartItemActions(container, cart);
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
                if (window.ShopToast) window.ShopToast.success("کوپن اعمال شد");
                renderCart(data, getCurrency());
            } else {
                const err = data.detail || "کوپن نامعتبر است";
                if (msg) msg.textContent = err;
                if (window.ShopToast) window.ShopToast.error(err);
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
                if (window.ShopToast) window.ShopToast.success("کارت هدیه اعمال شد");
                renderCart(data, getCurrency());
            } else {
                const err = data.detail || "کارت هدیه نامعتبر است";
                if (msg) msg.textContent = err;
                if (window.ShopToast) window.ShopToast.error(err);
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
        }).then(({ ok, status, data }) => {
            if (status === 401) {
                requireLogin();
                return { ok: false, authRequired: true, error: data.detail || "ورود الزامی است" };
            }
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
            let variantId = btn.dataset.variant ? Number(btn.dataset.variant) : null;
            let quantity = 1;

            // Prefer live Alpine state (multi-variant + qty) when present
            const alpineHost = btn.closest("[x-data]");
            if (alpineHost && alpineHost._x_dataStack && alpineHost._x_dataStack.length) {
                const state = alpineHost._x_dataStack[0];
                if (state && state.selectedVariant && state.selectedVariant.id) {
                    variantId = Number(state.selectedVariant.id);
                }
                if (state && state.qty) {
                    quantity = Math.max(1, Number(state.qty) || 1);
                }
            }

            // Pulse / data-attribute qty (set by qty.js / variants.js)
            if (btn.dataset.quantity) {
                quantity = Math.max(1, Number(btn.dataset.quantity) || quantity);
            }

            if (btn.disabled || btn.classList.contains("is-disabled")) return;
            if (!isLoggedIn()) {
                requireLogin();
                return;
            }
            btn.disabled = true;
            addToCart(slug, variantId, quantity).then((result) => {
                if (result.authRequired) return;
                btn.disabled = false;
                if (result.ok) {
                    const label = btn.querySelector("span") || btn;
                    const original = label.textContent;
                    label.textContent = "اضافه شد";
                    setTimeout(() => { label.textContent = original; }, 1500);
                } else if (window.ShopToast) {
                    window.ShopToast.error(result.error || "خطا");
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
