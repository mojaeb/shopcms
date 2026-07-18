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
        return fetch(API + path, {
            credentials: "same-origin",
            ...options,
            headers,
        }).then(async (res) => ({ ok: res.ok, status: res.status, data: await res.json() }));
    }

    function formatMoney(value, currency) {
        if (window.ShopMoney) return window.ShopMoney.formatMoney(value, currency);
        return Number(value || 0).toLocaleString("en-US") + (currency ? " " + currency : "");
    }

    function updateWishlistBadge(count) {
        document.querySelectorAll("[data-wishlist-count]").forEach((el) => {
            el.textContent = count;
            el.style.display = count > 0 ? "inline-block" : "none";
        });
    }

    function refreshCount() {
        apiFetch("/count").then(({ ok, data }) => {
            if (ok && data.enabled) updateWishlistBadge(data.count || 0);
        });
    }

    function renderWishlist(items, currency) {
        const container = document.getElementById("wishlist-container");
        if (!container) return;

        if (!items.length) {
            container.innerHTML = '<div class="empty-state card">لیست علاقه‌مندی‌ها خالی است.</div>';
            return;
        }

        container.innerHTML = `<div class="wishlist-grid">${items.map((p) => `
            <div class="card wishlist-card" data-product-id="${p.id}" data-product-slug="${p.slug}">
                <a href="/product/${p.slug}/">
                    ${p.image ? `<img src="${p.image}" alt="${p.name}">` : ""}
                    <h3 style="margin-top:0.75rem;">${p.name}</h3>
                    <p style="color:var(--accent); font-weight:bold;">${formatMoney(p.base_price, currency)}</p>
                </a>
                <div class="wishlist-actions">
                    <button type="button" class="btn btn-outline remove-wishlist" data-slug="${p.slug}">حذف</button>
                    ${p.in_stock ? `<button type="button" class="btn add-from-wishlist" data-slug="${p.slug}">افزودن به سبد</button>` : '<span class="muted">ناموجود</span>'}
                </div>
            </div>
        `).join("")}</div>`;

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
            if (status === 401) {
                container.innerHTML = '<div class="empty-state card">برای مشاهده علاقه‌مندی‌ها <a href="/login/">وارد شوید</a>.</div>';
                return;
            }
            if (!ok) {
                container.innerHTML = '<div class="empty-state card">علاقه‌مندی‌ها در دسترس نیست.</div>';
                return;
            }
            const currency = document.getElementById("wishlist-page")?.dataset.currency || "";
            renderWishlist(data, currency);
            updateWishlistBadge(data.length);
        });
    }

    function removeItem(slug) {
        apiFetch("/remove", {
            method: "POST",
            body: JSON.stringify({ product_slug: slug }),
        }).then(({ ok, data }) => {
            if (ok) {
                updateWishlistBadge(data.count || 0);
                loadWishlist();
            }
        });
    }

    function toggleWishlist(slug, button) {
        apiFetch("/toggle", {
            method: "POST",
            body: JSON.stringify({ product_slug: slug }),
        }).then(({ ok, status, data }) => {
            if (status === 401) {
                alert("برای افزودن به علاقه‌مندی‌ها وارد شوید.");
                return;
            }
            if (!ok) return;
            updateWishlistBadge(data.count || 0);
            if (button) {
                button.classList.toggle("active", data.in_wishlist);
                button.textContent = data.in_wishlist ? "♥ در علاقه‌مندی‌ها" : "♡ افزودن به علاقه‌مندی";
            }
        });
    }

    function initProductButtons() {
        document.querySelectorAll("[data-toggle-wishlist]").forEach((btn) => {
            if (btn.dataset.wishlistBound) return;
            btn.dataset.wishlistBound = "1";
            const slug = btn.dataset.product;
            apiFetch(`/check/${slug}`).then(({ ok, data }) => {
                if (ok && data.in_wishlist) {
                    btn.classList.add("active");
                    btn.textContent = "♥ در علاقه‌مندی‌ها";
                }
            });
            btn.addEventListener("click", () => toggleWishlist(slug, btn));
        });
    }

    if (document.getElementById("wishlist-page")) {
        loadWishlist();
    } else {
        refreshCount();
    }

    initProductButtons();

    window.ShopWishlist = { toggleWishlist, refreshCount, loadWishlist };
})();
