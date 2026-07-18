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
        return Number(v || 0).toLocaleString("en-US") + (currency ? " " + currency : "");
    }

    function setMoney(elId, value) {
        const el = document.getElementById(elId);
        if (!el) return;
        el.innerHTML = formatMoney(value);
    }

    function canPay() {
        return selectedAddressId && selectedShipping && selectedGateway;
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
        document.getElementById("checkout-submit").disabled = !canPay();
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

    function loadCart() {
        apiFetch("/api/v1/cart/").then(({ ok, data }) => {
            if (ok) {
                cartSubtotal = Number(data.subtotal || 0) - Number(data.discount || 0);
                setMoney("cart-subtotal", cartSubtotal);
                refreshTaxPreview();
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

    function loadAddresses() {
        apiFetch("/api/v1/addresses/").then(({ ok, status, data }) => {
            const el = document.getElementById("checkout-address");
            if (status === 401) {
                el.innerHTML = '<p class="muted">برای تسویه وارد شوید.</p>';
                return;
            }
            if (!ok || !data.length) {
                el.innerHTML = '<p class="muted">آدرسی ثبت نشده. <a href="/addresses/">افزودن آدرس</a></p>';
                return;
            }

            const auto = data.length === 1 ? data[0] : data.find((a) => a.is_default);
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
        if (!canPay()) return;
        const msg = document.getElementById("checkout-message");
        msg.textContent = "در حال انتقال به درگاه...";
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
                msg.textContent = data.detail || "خطا در ایجاد پرداخت";
            }
        });
    });

    loadCart();
    loadAddresses();
    loadGateways();
})();
