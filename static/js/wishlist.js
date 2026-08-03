(function () {
    const API = "/api/v1/wishlist";

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

    function formatMoney(value, currency) {
        if (window.ShopMoney) return window.ShopMoney.formatMoney(value, currency);
        return Number(value || 0).toLocaleString("fa-IR") + (currency ? " " + currency : "");
    }

    function refreshIcons() {
        if (!window.lucide || typeof window.lucide.createIcons !== "function") return;
        window.lucide.createIcons({
            attrs: { "stroke-width": 1.75 },
            nameAttr: "data-lucide",
        });
    }

    function updateWishlistBadge(count) {
        document.querySelectorAll("[data-wishlist-count]").forEach((el) => {
            el.textContent = count;
            el.style.display = count > 0 ? "" : "none";
        });
    }

    function setWishlistButtonState(button, inWishlist) {
        if (!button) return;
        const active = !!inWishlist;
        button.classList.toggle("is-active", active);
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", active ? "true" : "false");

        const label = button.querySelector("[data-wishlist-label]");
        if (label) {
            label.textContent = active ? "در علاقه‌مندی‌ها" : (label.dataset.idleLabel || "علاقه‌مندی");
        } else if (!button.querySelector("i, svg")) {
            button.textContent = active ? "♥ در علاقه‌مندی‌ها" : "♡ افزودن به علاقه‌مندی";
        } else {
            // Keep icon; update trailing text nodes carefully
            const nodes = Array.from(button.childNodes);
            nodes.forEach((node) => {
                if (node.nodeType === Node.TEXT_NODE && node.textContent.trim()) {
                    node.textContent = active ? " در علاقه‌مندی‌ها" : " علاقه‌مندی";
                }
            });
        }

        const icon = button.querySelector("[data-lucide]");
        if (icon) {
            icon.setAttribute("data-lucide", "heart");
            refreshIcons();
        }
    }

    function errorMessage(data, fallback) {
        if (!data) return fallback;
        if (typeof data.detail === "string") return data.detail;
        if (Array.isArray(data.detail) && data.detail[0]) {
            return data.detail[0].msg || fallback;
        }
        return fallback;
    }

    function requireLogin() {
        const next = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = "/login/?next=" + next;
    }

    function renderWishlist(items, currency) {
        const container = document.getElementById("wishlist-container");
        if (!container) return;
        const isPolished =
            document.body.classList.contains("theme-nextshop") ||
            document.body.classList.contains("theme-pulse") ||
            document.body.classList.contains("theme-gohar");

        if (!items.length) {
            container.innerHTML = isPolished
                ? '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="heart"></i></div><strong>لیست علاقه‌مندی خالی است</strong><p>محصولات موردعلاقه را ذخیره کنید تا بعداً راحت‌تر بخرید.</p><a class="ns-btn" href="/products/">مشاهده محصولات</a></div>'
                : '<div class="empty-state card">لیست علاقه‌مندی‌ها خالی است.</div>';
            if (isPolished) refreshIcons();
            return;
        }

        if (isPolished) {
            container.innerHTML = `<div class="ns-products-grid">${items
                .map(
                    (p) => `
                <div class="ns-card wishlist-card" data-product-id="${p.id}" data-product-slug="${p.slug}" style="padding:0.5rem;">
                    <a href="/product/${p.slug}/" class="ns-card" style="border:none;box-shadow:none;padding:0;">
                        <div class="ns-card-media">
                            ${p.image ? `<img src="${p.image}" alt="${p.name}" loading="lazy">` : '<div class="ns-card-placeholder"><i data-lucide="package"></i></div>'}
                        </div>
                        <div class="ns-card-body">
                            <h3 class="ns-card-title">${p.name}</h3>
                            <div class="ns-price"><strong>${formatMoney(p.base_price, currency)}</strong></div>
                        </div>
                    </a>
                    <div class="wishlist-actions" style="display:flex;gap:0.5rem;padding:0.5rem;flex-wrap:wrap;">
                        <button type="button" class="ns-btn ns-btn--ghost remove-wishlist" data-slug="${p.slug}">حذف</button>
                        ${
                            p.in_stock
                                ? `<button type="button" class="ns-btn add-from-wishlist" data-slug="${p.slug}">افزودن به سبد</button>`
                                : '<span class="muted">ناموجود</span>'
                        }
                    </div>
                </div>
            `
                )
                .join("")}</div>`;
        } else {
            container.innerHTML = `<div class="wishlist-grid">${items
                .map(
                    (p) => `
            <div class="card wishlist-card" data-product-id="${p.id}" data-product-slug="${p.slug}">
                <a href="/product/${p.slug}/">
                    ${p.image ? `<img src="${p.image}" alt="${p.name}">` : ""}
                    <h3 style="margin-top:0.75rem;">${p.name}</h3>
                    <p style="color:var(--accent); font-weight:bold;">${formatMoney(p.base_price, currency)}</p>
                </a>
                <div class="wishlist-actions">
                    <button type="button" class="btn btn-outline remove-wishlist" data-slug="${p.slug}">حذف</button>
                    ${
                        p.in_stock
                            ? `<button type="button" class="btn add-from-wishlist" data-slug="${p.slug}">افزودن به سبد</button>`
                            : '<span class="muted">ناموجود</span>'
                    }
                </div>
            </div>
        `
                )
                .join("")}</div>`;
        }

        refreshIcons();

        container.querySelectorAll(".remove-wishlist").forEach((btn) => {
            btn.addEventListener("click", () => removeItem(btn.dataset.slug));
        });
        container.querySelectorAll(".add-from-wishlist").forEach((btn) => {
            btn.addEventListener("click", () => {
                if (window.ShopCart) {
                    window.ShopCart.addToCart(btn.dataset.slug, null, 1);
                }
            });
        });
    }

    function loadWishlist() {
        apiFetch("/").then(({ ok, status, data }) => {
            const container = document.getElementById("wishlist-container");
            if (!container) return;
            const isPolished =
                document.body.classList.contains("theme-nextshop") ||
                document.body.classList.contains("theme-pulse") ||
                document.body.classList.contains("theme-gohar");
            if (status === 401) {
                container.innerHTML = isPolished
                    ? '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="log-in"></i></div><strong>ورود لازم است</strong><p>برای مشاهده علاقه‌مندی‌ها وارد شوید.</p><a class="ns-btn" href="/login/?next=/wishlist/">ورود</a></div>'
                    : '<div class="empty-state card">برای مشاهده علاقه‌مندی‌ها <a href="/login/?next=/wishlist/">وارد شوید</a>.</div>';
                if (isPolished) refreshIcons();
                return;
            }
            if (!ok) {
                container.innerHTML = isPolished
                    ? `<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="alert-circle"></i></div><strong>موقتاً در دسترس نیست</strong><p>${errorMessage(data, "علاقه‌مندی‌ها در دسترس نیست.")}</p></div>`
                    : `<div class="empty-state card">${errorMessage(data, "علاقه‌مندی‌ها در دسترس نیست.")}</div>`;
                if (isPolished) refreshIcons();
                return;
            }
            const currency = document.getElementById("wishlist-page")?.dataset.currency || "";
            renderWishlist(Array.isArray(data) ? data : [], currency);
            updateWishlistBadge(Array.isArray(data) ? data.length : 0);
        });
    }

    function removeItem(slug) {
        apiFetch("/remove", {
            method: "POST",
            body: JSON.stringify({ product_slug: slug }),
        }).then(({ ok, status, data }) => {
            if (status === 401) {
                requireLogin();
                return;
            }
            if (!ok) {
                if (window.ShopToast) {
                    window.ShopToast.error(errorMessage(data, "حذف از علاقه‌مندی‌ها انجام نشد."));
                }
                return;
            }
            updateWishlistBadge(data.count || 0);
            loadWishlist();
        });
    }

    function toggleWishlist(slug, button) {
        if (!slug) return;
        if (button) button.disabled = true;

        apiFetch("/toggle", {
            method: "POST",
            body: JSON.stringify({ product_slug: slug }),
        })
            .then(({ ok, status, data }) => {
                if (status === 401) {
                    requireLogin();
                    return;
                }
                if (!ok) {
                    if (window.ShopToast) {
                        window.ShopToast.error(errorMessage(data, "افزودن به علاقه‌مندی‌ها انجام نشد."));
                    }
                    return;
                }
                updateWishlistBadge(data.count || 0);
                setWishlistButtonState(button, data.in_wishlist);
            })
            .finally(() => {
                if (button) button.disabled = false;
            });
    }

    function initProductButtons() {
        document.querySelectorAll("[data-toggle-wishlist]").forEach((btn) => {
            if (btn.dataset.wishlistBound) return;
            btn.dataset.wishlistBound = "1";
            const slug = btn.dataset.product;
            if (!slug) return;

            apiFetch(`/check/${encodeURIComponent(slug)}`).then(({ ok, data }) => {
                if (ok && data && data.in_wishlist) {
                    setWishlistButtonState(btn, true);
                }
            });

            btn.addEventListener("click", (event) => {
                event.preventDefault();
                toggleWishlist(slug, btn);
            });
        });
    }

    function refreshCount() {
        apiFetch("/count").then(({ ok, data }) => {
            if (ok && data.enabled) updateWishlistBadge(data.count || 0);
        });
    }

    if (document.getElementById("wishlist-page")) {
        loadWishlist();
    } else {
        refreshCount();
    }

    initProductButtons();

    window.ShopWishlist = { toggleWishlist, refreshCount, loadWishlist, setWishlistButtonState };
})();
