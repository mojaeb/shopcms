(function () {
    const page = document.getElementById("checkout-page");
    if (!page) return;

    const currency = page.dataset.currency || "";
    let selectedAddressId = null;
    let selectedShipping = null;
    let selectedGateway = null;
    let cartSubtotal = 0;
    let cartTax = 0;
    let taxEnabled = false;
    let gateways = [];

    function getCookie(name) {
        const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
        return match ? decodeURIComponent(match[2]) : "";
    }

    function apiFetch(url, options = {}) {
        const headers = {
            "Content-Type": "application/json",
            Accept: "application/json",
            ...(options.headers || {}),
        };
        const csrf = getCookie("csrftoken");
        if (csrf) headers["X-CSRFToken"] = csrf;
        return fetch(url, { credentials: "same-origin", ...options, headers })
            .then(async (res) => ({ ok: res.ok, status: res.status, data: await res.json() }));
    }

    function formatMoney(v) {
        if (window.ShopMoney) return window.ShopMoney.formatMoney(v, currency);
        return Number(v || 0).toLocaleString("fa-IR") + (currency ? " " + currency : "");
    }

    function setMoney(elId, value) {
        const el = document.getElementById(elId);
        if (!el) return;
        el.innerHTML = formatMoney(value);
    }

    function canPay() {
        return selectedAddressId && selectedShipping && selectedGateway;
    }

    function notify(message, isError, type) {
        const msg = document.getElementById("checkout-message");
        if (msg) {
            msg.textContent = message;
            msg.classList.toggle("is-error", !!isError);
        }
        if (window.ShopToast) {
            const toastType = type || (isError ? "error" : "success");
            window.ShopToast.show(message, { type: toastType });
        }
    }

    function updateTotals() {
        const shipping = selectedShipping ? Number(selectedShipping.price) : 0;
        setMoney("shipping-cost", shipping);
        const taxRow = document.getElementById("tax-row");
        if (taxEnabled && cartTax > 0) {
            taxRow.style.display = "";
            setMoney("tax-cost", cartTax);
        } else {
            taxRow.style.display = "none";
        }
        setMoney("checkout-total", cartSubtotal + shipping + cartTax);
        const submit = document.getElementById("checkout-submit");
        if (submit) submit.disabled = false;
    }

    function refreshTaxPreview() {
        const shipping = selectedShipping ? Number(selectedShipping.price) : 0;
        apiFetch("/api/v1/taxes/preview", {
            method: "POST",
            body: JSON.stringify({ shipping_price: shipping }),
        }).then(({ ok, data }) => {
            if (!ok) return;
            taxEnabled = data.enabled;
            cartTax = Number(data.tax || 0);
            updateTotals();
        });
    }

    function escapeHtml(str) {
        return String(str ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function renderCheckoutItems(items) {
        const el = document.getElementById("checkout-items");
        if (!el) return;

        if (!items || !items.length) {
            el.innerHTML = '<p class="muted">سبد خرید خالی است. <a href="/cart/">بازگشت به سبد</a></p>';
            return;
        }

        el.innerHTML = items.map((item) => {
            const name = escapeHtml(item.product_name);
            const variant = item.variant_label
                ? `<p class="ns-variant-chip checkout-item-meta"><i data-lucide="layers" aria-hidden="true"></i>${escapeHtml(item.variant_label)}</p>`
                : "";
            const img = item.image
                ? `<img src="${escapeHtml(item.image)}" alt="${name}" class="cart-item-img checkout-item-img">`
                : `<div class="checkout-item-img checkout-item-img--empty" aria-hidden="true"></div>`;
            return `
                <div class="checkout-item cart-item" data-item-id="${item.id}">
                    <div class="cart-item-info checkout-item-info">
                        ${img}
                        <div class="checkout-item-body">
                            <h3 class="checkout-item-title">${name}</h3>
                            ${variant}
                            <p class="muted checkout-item-meta">تعداد: ${Number(item.quantity) || 0}</p>
                        </div>
                    </div>
                    <p class="line-total checkout-item-total">${formatMoney(item.line_total)}</p>
                </div>
            `;
        }).join("");
        if (window.lucide) window.lucide.createIcons();
    }

    function loadCart() {
        apiFetch("/api/v1/cart/").then(({ ok, data }) => {
            if (ok) {
                cartSubtotal = Number(data.subtotal || 0) - Number(data.discount || 0);
                setMoney("cart-subtotal", cartSubtotal);
                renderCheckoutItems(data.items || []);
                refreshTaxPreview();
            } else {
                renderCheckoutItems([]);
            }
        });
    }

    function loadGateways() {
        apiFetch("/api/v1/payments/gateways").then(({ ok, data }) => {
            const el = document.getElementById("payment-gateways");
            if (!ok || !data.length) {
                el.innerHTML = '<p class="muted">درگاه پرداختی فعال نیست.</p>';
                return;
            }
            gateways = data;
            const defaultGw = data.find((g) => g.is_default) || data[0];
            selectedGateway = defaultGw.codename;
            el.innerHTML = data.map((g) => `
                <label class="shipping-option ${g.codename === selectedGateway ? "selected" : ""}">
                    <input type="radio" name="gateway" value="${g.codename}" ${g.codename === selectedGateway ? "checked" : ""}>
                    <div><strong>${g.label}</strong></div>
                </label>
            `).join("");
            el.querySelectorAll('input[name="gateway"]').forEach((input) => {
                input.addEventListener("change", () => {
                    selectedGateway = input.value;
                    el.querySelectorAll(".shipping-option").forEach((o) => o.classList.remove("selected"));
                    input.closest(".shipping-option").classList.add("selected");
                    updateTotals();
                });
            });
            updateTotals();
        });
    }

    function loadAddresses(options = {}) {
        const preferId = options.selectId != null ? Number(options.selectId) : null;

        apiFetch("/api/v1/addresses/").then(({ ok, status, data }) => {
            const el = document.getElementById("checkout-address");
            if (status === 401) {
                el.innerHTML =
                    '<p class="muted">برای تسویه وارد شوید. <a href="/login/?next=' +
                    encodeURIComponent(window.location.pathname + window.location.search) +
                    '">ورود</a></p>';
                return;
            }
            if (!ok || !data.length) {
                const hasModal = !!document.getElementById("checkout-address-modal");
                el.innerHTML = hasModal
                    ? '<p class="muted">آدرسی ثبت نشده. روی «افزودن آدرس» کلیک کنید.</p>'
                    : '<p class="muted">آدرسی ثبت نشده. <a href="/addresses/">افزودن آدرس</a></p>';
                selectedAddressId = null;
                return;
            }

            let auto = null;
            if (preferId != null) {
                auto = data.find((a) => Number(a.id) === preferId) || null;
            }
            if (!auto) {
                auto = data.length === 1 ? data[0] : data.find((a) => a.is_default);
            }

            el.innerHTML = data.map((a) => `
                <label class="shipping-option ${auto && auto.id === a.id ? "selected" : ""}">
                    <input type="radio" name="address" value="${a.id}" ${auto && auto.id === a.id ? "checked" : ""}>
                    <div>
                        <strong>${a.full_name}</strong> — ${a.city}
                        <p class="muted" style="font-size:0.85rem;">${a.full_address}</p>
                    </div>
                </label>
            `).join("");

            if (auto) {
                selectedAddressId = auto.id;
                loadShipping(auto.id);
            }

            el.querySelectorAll('input[name="address"]').forEach((input) => {
                input.addEventListener("change", () => {
                    selectedAddressId = Number(input.value);
                    el.querySelectorAll(".shipping-option").forEach((o) => o.classList.remove("selected"));
                    input.closest(".shipping-option").classList.add("selected");
                    loadShipping(selectedAddressId);
                });
            });
        });
    }

    function initAddressModal() {
        const modal = document.getElementById("checkout-address-modal");
        const openBtn = document.getElementById("checkout-add-address-btn");
        const form = document.getElementById("checkout-address-form");
        if (!modal || !openBtn || !form) return;

        let lastFocus = null;

        function getFocusable() {
            return Array.from(
                modal.querySelectorAll(
                    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
                )
            ).filter((el) => !el.hasAttribute("disabled") && el.getAttribute("aria-hidden") !== "true");
        }

        function openModal() {
            lastFocus = document.activeElement;
            modal.hidden = false;
            document.body.classList.add("ps-modal-open");
            const first = form.querySelector("input, textarea, select, button");
            (first || openBtn).focus();
            if (window.lucide) window.lucide.createIcons();
        }

        function closeModal() {
            if (modal.hidden) return;
            modal.hidden = true;
            document.body.classList.remove("ps-modal-open");
            const msg = document.getElementById("checkout-address-form-message");
            if (msg) msg.textContent = "";
            form.reset();
            if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
        }

        openBtn.addEventListener("click", openModal);

        modal.querySelectorAll("[data-modal-dismiss]").forEach((el) => {
            el.addEventListener("click", closeModal);
        });

        document.addEventListener("keydown", (e) => {
            if (modal.hidden) return;
            if (e.key === "Escape") {
                e.preventDefault();
                closeModal();
                return;
            }
            if (e.key !== "Tab") return;
            const focusable = getFocusable();
            if (!focusable.length) return;
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (e.shiftKey && document.activeElement === first) {
                e.preventDefault();
                last.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        });

        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const msg = document.getElementById("checkout-address-form-message");
            const payload = Object.fromEntries(new FormData(form).entries());
            payload.is_default = !!form.querySelector('[name="is_default"]')?.checked;

            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) submitBtn.disabled = true;
            if (msg) msg.textContent = "در حال ذخیره...";

            apiFetch("/api/v1/addresses/", {
                method: "POST",
                body: JSON.stringify(payload),
            }).then(({ ok, data }) => {
                if (submitBtn) submitBtn.disabled = false;
                if (ok) {
                    if (msg) msg.textContent = "";
                    closeModal();
                    loadAddresses({ selectId: data.id });
                    notify("آدرس ذخیره شد");
                } else if (msg) {
                    msg.textContent = data.detail || "خطا در ذخیره آدرس";
                }
            }).catch(() => {
                if (submitBtn) submitBtn.disabled = false;
                if (msg) msg.textContent = "خطا در ذخیره آدرس";
            });
        });
    }

    function loadShipping(addressId) {
        const el = document.getElementById("shipping-options");
        el.innerHTML = '<p class="muted">در حال محاسبه هزینه ارسال...</p>';

        apiFetch("/api/v1/shipping/calculate", {
            method: "POST",
            body: JSON.stringify({ address_id: addressId }),
        }).then(({ ok, data }) => {
            if (!ok || !data.quotes || !data.quotes.length) {
                el.innerHTML = '<p class="muted">روش ارسالی یافت نشد.</p>';
                selectedShipping = null;
                updateTotals();
                return;
            }

            el.innerHTML = data.quotes.map((q, i) => `
                <label class="shipping-option ${i === 0 ? "selected" : ""}">
                    <input type="radio" name="shipping" value="${q.method_id}" data-price="${q.price}" ${i === 0 ? "checked" : ""}>
                    <div>
                        <strong>${q.name}</strong>
                        <p class="muted" style="font-size:0.85rem;">
                            ${q.is_free ? "رایگان" : formatMoney(q.price)}
                            — تحویل حدود ${q.estimated_days} روز
                        </p>
                    </div>
                </label>
            `).join("");

            selectedShipping = data.quotes[0];
            refreshTaxPreview();

            el.querySelectorAll('input[name="shipping"]').forEach((input) => {
                input.addEventListener("change", () => {
                    const quote = data.quotes.find((q) => String(q.method_id) === input.value);
                    selectedShipping = quote;
                    el.querySelectorAll(".shipping-option").forEach((o) => o.classList.remove("selected"));
                    input.closest(".shipping-option").classList.add("selected");
                    refreshTaxPreview();
                });
            });
        });
    }

    document.getElementById("checkout-submit")?.addEventListener("click", () => {
        if (!selectedAddressId) {
            notify("آدرس وارد نشده", true);
            return;
        }
        if (!selectedShipping) {
            notify("روش ارسال انتخاب نشده", true);
            return;
        }
        if (!selectedGateway) {
            notify("درگاه پرداخت انتخاب نشده", true);
            return;
        }
        if (!canPay()) return;

        notify("در حال انتقال به درگاه...", false, "info");
        apiFetch("/api/v1/payments/create", {
            method: "POST",
            body: JSON.stringify({
                gateway: selectedGateway,
                address_id: selectedAddressId,
                shipping_method_id: selectedShipping.method_id,
                shipping_price: Number(selectedShipping.price),
            }),
        }).then(({ ok, data }) => {
            if (ok && data.payment_url) {
                window.location.href = data.payment_url;
            } else {
                notify(data.detail || "خطا در ایجاد پرداخت", true);
            }
        });
    });

    initAddressModal();
    loadCart();
    loadAddresses();
    loadGateways();
})();
