(function () {
    const root = document.getElementById("product-catalog");
    if (!root) return;

    const apiBase = root.dataset.apiBase || "/api/v1/products/";
    const currency = root.dataset.currency || "";
    const categorySlug = root.dataset.category || "";
    const initialQuery = root.dataset.query || "";

    const form = document.getElementById("product-filters-form");
    const resultsEl = document.getElementById("product-results");
    const countEl = document.getElementById("product-count");
    const paginationEl = document.getElementById("product-pagination");
    const sortEl = document.getElementById("filter-sort");

    let currentPage = 1;
    let debounceTimer = null;

    function getCheckedValues(name) {
        return Array.from(form.querySelectorAll(`input[name="${name}"]:checked`)).map((el) => el.value);
    }

    function buildQuery(page) {
        const params = new URLSearchParams();
        const search = form.querySelector('[name="search"]')?.value?.trim() || initialQuery;
        if (search) params.set("search", search);
        if (categorySlug) params.set("category", categorySlug);

        const brands = getCheckedValues("brand");
        if (brands.length === 1) params.set("brand", brands[0]);
        else if (brands.length > 1) params.set("brands", brands.join(","));

        const minPrice = form.querySelector('[name="min_price"]')?.value;
        const maxPrice = form.querySelector('[name="max_price"]')?.value;
        if (minPrice) params.set("min_price", minPrice);
        if (maxPrice) params.set("max_price", maxPrice);

        const attrInputs = form.querySelectorAll('[data-attr-slug]:checked');
        if (attrInputs.length) {
            const attrs = Array.from(attrInputs).map(
                (el) => `${el.dataset.attrSlug}:${el.value}`
            );
            params.set("attributes", attrs.join(","));
        }

        if (form.querySelector('[name="in_stock"]')?.checked) {
            params.set("in_stock", "true");
        }
        if (sortEl?.value) params.set("sort", sortEl.value);
        params.set("page", String(page || 1));
        return params;
    }

    function isModern() {
        return document.body.classList.contains("theme-modern");
    }

    function isNextshop() {
        return document.body.classList.contains("theme-nextshop");
    }

    function isPulse() {
        return document.body.classList.contains("theme-pulse");
    }

    function renderProductCard(product) {
        const money = window.ShopMoney
            ? window.ShopMoney.formatMoney(product.base_price, currency)
            : Number(product.base_price || 0).toLocaleString("fa-IR") + " " + currency;

        if (isPulse()) {
            const image = product.image
                ? `<img src="${product.image}" alt="${product.name}" loading="lazy">`
                : '<div class="ps-card-placeholder"><i data-lucide="package"></i></div>';
            const cat = product.category
                ? `<span class="ps-card-cat">${product.category}</span>`
                : '<span class="ps-card-cat">&nbsp;</span>';
            const oos = product.in_stock
                ? ""
                : '<div class="ps-card-oos"><span>ناموجود</span></div>';
            let badge = "";
            if (product.discount_percent) {
                const pct = window.ShopMoney
                    ? window.ShopMoney.formatAmount(product.discount_percent)
                    : product.discount_percent;
                badge = `<span class="ps-badge ps-badge--sale ps-card-badge">${pct}٪</span>`;
            } else if (product.is_featured) {
                badge = '<span class="ps-badge ps-badge--feat ps-card-badge">ویژه</span>';
            }
            const compare = product.compare_price && product.discount_percent
                ? `<s class="ps-price-was">${window.ShopMoney ? window.ShopMoney.formatMoney(product.compare_price, currency) : product.compare_price}</s>`
                : '<span class="ps-price-was ps-price-was--empty" aria-hidden="true">&nbsp;</span>';
            return `
                <a href="/product/${product.slug}/" class="ps-card">
                    <div class="ps-card-media">${image}${badge}</div>
                    <div class="ps-card-body">
                        ${cat}
                        <h3 class="ps-card-title">${product.name}</h3>
                        <div class="ps-price">${compare}<strong class="ps-price-now">${money}</strong></div>
                    </div>
                    ${oos}
                </a>
            `;
        }

        if (isNextshop()) {
            const image = product.image
                ? `<img src="${product.image}" alt="${product.name}" loading="lazy">`
                : '<div class="ns-card-placeholder"><i data-lucide="package"></i></div>';
            const cat = product.category
                ? `<span class="ns-card-cat">${product.category}</span>`
                : '<span class="ns-card-cat">&nbsp;</span>';
            const oos = product.in_stock
                ? ""
                : '<div class="ns-card-oos"><span>ناموجود</span></div>';
            let badge = "";
            if (product.discount_percent) {
                const pct = window.ShopMoney
                    ? window.ShopMoney.formatAmount(product.discount_percent)
                    : product.discount_percent;
                badge = `<span class="ns-badge ns-badge--sale ns-card-badge">${pct}٪</span>`;
            } else if (product.is_featured) {
                badge = '<span class="ns-badge ns-badge--feat ns-card-badge">ویژه</span>';
            }
            const compare = product.compare_price && product.discount_percent
                ? `<s>${window.ShopMoney ? window.ShopMoney.formatMoney(product.compare_price, currency) : product.compare_price}</s>`
                : '<span class="ns-price-was ns-price-was--empty" aria-hidden="true">&nbsp;</span>';
            return `
                <a href="/product/${product.slug}/" class="ns-card">
                    <div class="ns-card-media">${image}${badge}</div>
                    <div class="ns-card-body">
                        ${cat}
                        <h3 class="ns-card-title">${product.name}</h3>
                        <div class="ns-card-meta">
                            <div class="ns-price">${compare}<strong>${money}</strong></div>
                        </div>
                    </div>
                    ${oos}
                </a>
            `;
        }

        if (isModern()) {
            const stockPill = product.in_stock ? "" : '<span class="vg-pill">ناموجود</span>';
            const featPill = product.is_featured ? '<span class="vg-pill vg-pill--feat">ویژه</span>' : "";
            const image = product.image
                ? `<img src="${product.image}" alt="${product.name}" loading="lazy">`
                : '<div class="vg-product-placeholder"></div>';
            const cat = product.category
                ? `<span class="vg-product-cat">${product.category}</span>`
                : "";
            return `
                <a href="/product/${product.slug}/" class="vg-product" data-vg-reveal>
                    <div class="vg-product-media">
                        ${image}
                        ${stockPill}${featPill}
                        <span class="vg-product-hover"><i data-lucide="eye"></i> مشاهده</span>
                    </div>
                    <div class="vg-product-body">
                        ${cat}
                        <h3>${product.name}</h3>
                        <p class="vg-price"><span>${money}</span></p>
                    </div>
                </a>
            `;
        }

        const stockBadge = product.in_stock
            ? ""
            : '<span class="badge" style="background:#999;">ناموجود</span>';
        const image = product.image
            ? `<img src="${product.image}" alt="${product.name}" style="width:100%;height:180px;object-fit:cover;border-radius:4px;">`
            : "";
        return `
            <a href="/product/${product.slug}/" class="card product-card">
                ${image}
                <h3 style="margin-top:0.75rem;">${product.name}</h3>
                <p style="color:var(--accent);font-weight:bold;">${money}</p>
                ${stockBadge}
            </a>
        `;
    }

    function renderPagination(count, page) {
        const pageSize = 20;
        const totalPages = Math.ceil(count / pageSize) || 1;
        if (totalPages <= 1) {
            paginationEl.innerHTML = "";
            return;
        }
        let html = '<div class="pagination">';
        for (let i = 1; i <= totalPages; i += 1) {
            html += `<button type="button" class="btn${i === page ? "" : " btn-outline"}" data-page="${i}">${i}</button> `;
        }
        html += "</div>";
        paginationEl.innerHTML = html;
        paginationEl.querySelectorAll("[data-page]").forEach((btn) => {
            btn.addEventListener("click", () => {
                currentPage = Number(btn.dataset.page);
                fetchProducts(currentPage);
            });
        });
    }

    function fetchProducts(page) {
        const params = buildQuery(page);
        resultsEl.classList.add("loading");
        fetch(`${apiBase}?${params.toString()}`, {
            headers: { Accept: "application/json" },
        })
            .then((res) => res.json())
            .then((data) => {
                currentPage = data.page || page || 1;
                if (countEl) {
                    countEl.textContent = `${data.count || 0} محصول`;
                }
                if (!data.items || !data.items.length) {
                    resultsEl.innerHTML = isPulse()
                        ? '<div class="ps-empty"><p>محصولی یافت نشد.</p></div>'
                        : isNextshop()
                        ? '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="package-open"></i></div><strong>محصولی یافت نشد</strong><p>فیلترها را تغییر دهید یا عبارت دیگری جستجو کنید.</p></div>'
                        : isModern()
                        ? '<div class="vg-empty" data-vg-reveal><i data-lucide="package-open" class="vg-empty-icon"></i><p>محصولی یافت نشد.</p></div>'
                        : '<div class="empty-state card">محصولی یافت نشد.</div>';
                    if (isNextshop() && window.lucide) window.lucide.createIcons();
                } else {
                    const wrapClass = isPulse()
                        ? "ps-products-grid"
                        : isNextshop()
                        ? "ns-products-grid"
                        : isModern()
                        ? "vg-products vg-products--catalog"
                        : "grid";
                    resultsEl.innerHTML = `<div class="${wrapClass}">${data.items.map(renderProductCard).join("")}</div>`;
                }
                renderPagination(data.count || 0, currentPage);
                if (window.PulseTheme && typeof window.PulseTheme.refreshIcons === "function") {
                    window.PulseTheme.refreshIcons(resultsEl);
                } else if (window.lucide && typeof window.lucide.createIcons === "function") {
                    window.lucide.createIcons({
                        attrs: { "stroke-width": 1.75 },
                        nameAttr: "data-lucide",
                    });
                }
                if (window.ShopModern && typeof window.ShopModern.afterCatalogUpdate === "function") {
                    window.ShopModern.afterCatalogUpdate();
                }
            })
            .catch(() => {
                resultsEl.innerHTML = '<div class="empty-state card">خطا در بارگذاری محصولات.</div>';
            })
            .finally(() => resultsEl.classList.remove("loading"));
    }

    function scheduleFetch() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            currentPage = 1;
            fetchProducts(1);
        }, 300);
    }

    form.addEventListener("change", scheduleFetch);
    form.addEventListener("input", (e) => {
        if (e.target.name === "search" || e.target.name === "min_price" || e.target.name === "max_price") {
            scheduleFetch();
        }
    });
    form.addEventListener("submit", (e) => {
        e.preventDefault();
        currentPage = 1;
        fetchProducts(1);
    });
    if (sortEl) sortEl.addEventListener("change", scheduleFetch);

    document.getElementById("filter-reset")?.addEventListener("click", () => {
        form.reset();
        if (sortEl) sortEl.value = "newest";
        currentPage = 1;
        fetchProducts(1);
    });

    if (initialQuery && form.querySelector('[name="search"]')) {
        form.querySelector('[name="search"]').value = initialQuery;
    }
})();
