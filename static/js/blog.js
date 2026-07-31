(function () {
    const API = "/api/v1/blog";
    const isNextshop = document.body.classList.contains("theme-nextshop");
    const isPulse = document.body.classList.contains("theme-pulse");

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
        }).then(async (res) => {
            let data = null;
            try {
                data = await res.json();
            } catch (_) {
                data = {};
            }
            return { ok: res.ok, status: res.status, data };
        });
    }

    function escapeHtml(str) {
        return String(str || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function formatDate(iso) {
        if (!iso) return "";
        try {
            return new Date(iso).toLocaleDateString("fa-IR");
        } catch (_) {
            return "";
        }
    }

    function refreshIcons() {
        if (window.PulseTheme && typeof window.PulseTheme.refreshIcons === "function") {
            window.PulseTheme.refreshIcons();
        } else if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons();
        }
    }

    function emptyHtml(text, opts) {
        opts = opts || {};
        const title = opts.title || "";
        const icon = opts.icon || "inbox";
        const action = opts.action || "";
        if (isPulse) return `<div class="ps-empty"><p>${escapeHtml(text)}</p></div>`;
        if (isNextshop) {
            return (
                `<div class="ns-empty">` +
                `<div class="ns-empty-icon" aria-hidden="true"><i data-lucide="${icon}"></i></div>` +
                (title ? `<strong>${escapeHtml(title)}</strong>` : "") +
                `<p>${escapeHtml(text)}</p>` +
                (action || "") +
                `</div>`
            );
        }
        return `<div class="empty-state card">${escapeHtml(text)}</div>`;
    }

    function renderPostCard(post) {
        const title = escapeHtml(post.title);
        const excerpt = escapeHtml(post.excerpt || "");
        const category = escapeHtml(post.category || "");
        const date = formatDate(post.published_at);
        const slug = escapeHtml(post.slug);
        const image = post.featured_image ? escapeHtml(post.featured_image) : "";

        if (isPulse) {
            const media = image
                ? `<span class="ps-blog-card-media"><img src="${image}" alt="" loading="lazy"></span>`
                : `<span class="ps-blog-card-media ps-blog-card-media--empty" aria-hidden="true"></span>`;
            return `
            <a href="/blog/${slug}/" class="ps-blog-card">
                ${media}
                <span class="ps-blog-card-body">
                    <span class="ps-blog-card-meta">
                        ${category ? `<span>${category}</span>` : ""}
                        ${date ? `<time>${date}</time>` : ""}
                    </span>
                    <h3 class="ps-blog-card-title">${title}</h3>
                    ${excerpt ? `<p class="ps-blog-card-excerpt">${excerpt}</p>` : ""}
                    <span class="ps-section-link">ادامه مطلب <i data-lucide="arrow-left"></i></span>
                </span>
            </a>`;
        }

        if (isNextshop) {
            const media = image
                ? `<span class="ns-blog-card-media"><img src="${image}" alt="" loading="lazy"></span>`
                : `<span class="ns-blog-card-media ns-blog-card-media--empty" aria-hidden="true"></span>`;
            return `
            <a href="/blog/${slug}/" class="ns-blog-card">
                ${media}
                <span class="ns-blog-card-body">
                    <span class="ns-blog-card-meta">${category ? `<span>${category}</span>` : ""}${date ? `<time>${date}</time>` : ""}</span>
                    <h3 class="ns-blog-card-title">${title}</h3>
                    ${excerpt ? `<p class="ns-blog-card-excerpt">${excerpt}</p>` : ""}
                    <span class="ns-blog-card-more">ادامه مطلب <i data-lucide="arrow-left"></i></span>
                </span>
            </a>`;
        }

        const media = image
            ? `<span class="blog-card-media"><img src="${image}" alt="" loading="lazy"></span>`
            : "";
        return `
            <a href="/blog/${slug}/" class="card blog-card">
                ${media}
                <h3 style="margin-top:0.75rem;">${title}</h3>
                <p class="muted">${excerpt}</p>
                <p class="muted">${date}${category ? " — " + category : ""}</p>
            </a>`;
    }

    function loadCategories() {
        const el = document.getElementById("blog-categories");
        if (!el) return;
        apiFetch("/categories").then(({ ok, data }) => {
            if (!ok || !Array.isArray(data)) return;
            const filterClass = isPulse
                ? "ps-blog-filter"
                : isNextshop
                ? "ns-blog-filter"
                : "btn btn-outline blog-filter";
            el.classList.add(isPulse ? "ps-blog-filters" : isNextshop ? "ns-blog-filters" : "blog-filters");
            el.innerHTML =
                `<button type="button" class="${filterClass} is-active" data-category="">همه</button>` +
                data
                    .map(
                        (c) =>
                            `<button type="button" class="${filterClass}" data-category="${escapeHtml(c.slug)}">${escapeHtml(c.name)}</button>`
                    )
                    .join("");
            el.querySelectorAll("[data-category]").forEach((btn) => {
                btn.addEventListener("click", () => {
                    el.querySelectorAll("[data-category]").forEach((b) => b.classList.remove("is-active"));
                    btn.classList.add("is-active");
                    loadPosts(btn.dataset.category || "");
                });
            });
        });
    }

    function loadPosts(category) {
        const container = document.getElementById("blog-posts");
        if (!container) return;
        container.innerHTML = emptyHtml("لطفاً صبر کنید...", { title: "در حال بارگذاری", icon: "newspaper" });
        refreshIcons();

        const qs = category ? `?category=${encodeURIComponent(category)}` : "";
        apiFetch(`/posts${qs}`).then(({ ok, data }) => {
            if (!ok) {
                container.innerHTML = emptyHtml("وبلاگ موقتاً در دسترس نیست.", { title: "خطا", icon: "alert-circle" });
                refreshIcons();
                return;
            }
            const items = data.items || data || [];
            if (!items.length) {
                container.innerHTML = emptyHtml("هنوز مطلبی در این دسته منتشر نشده.", { title: "مطلبی نیست", icon: "newspaper" });
                refreshIcons();
                return;
            }
            const gridClass = isPulse ? "ps-blog-grid" : isNextshop ? "ns-blog-grid" : "blog-grid";
            container.innerHTML = `<div class="${gridClass}">${items.map(renderPostCard).join("")}</div>`;
            refreshIcons();
        });
    }

    function loadSinglePost(slug) {
        const container = document.getElementById("blog-post-content");
        if (!container) return;

        apiFetch(`/posts/${slug}`).then(({ ok, data }) => {
            if (!ok) {
                container.innerHTML = emptyHtml("این مطلب پیدا نشد یا حذف شده است.", { title: "مقاله یافت نشد", icon: "file-question" });
                refreshIcons();
                return;
            }
            document.title = (data.seo?.meta_title || data.title) + " - وبلاگ";
            const tags = (data.tags || [])
                .map((t) => {
                    const name = escapeHtml(t.name || t);
                    if (isPulse) return `<span class="ps-blog-tag">${name}</span>`;
                    return `<span class="ns-blog-tag">${name}</span>`;
                })
                .join("");

            if (isPulse) {
                container.innerHTML = `
                <article class="ps-blog-article">
                    ${
                        data.featured_image
                            ? `<div class="ps-blog-hero"><img src="${escapeHtml(data.featured_image)}" alt=""></div>`
                            : ""
                    }
                    <header class="ps-blog-article-head">
                        <a href="/blog/" class="ps-section-link"><i data-lucide="arrow-right"></i> بازگشت به وبلاگ</a>
                        <h1 class="ps-page-title">${escapeHtml(data.title)}</h1>
                        <div class="ps-blog-article-meta">
                            <span>${formatDate(data.published_at)}</span>
                            ${data.author ? `<span>${escapeHtml(data.author)}</span>` : ""}
                            ${data.category ? `<span>${escapeHtml(data.category)}</span>` : ""}
                        </div>
                        ${tags ? `<div class="ps-blog-tags">${tags}</div>` : ""}
                    </header>
                    <div class="ps-prose ps-blog-prose rich-content">${data.content || ""}</div>
                </article>`;
            } else if (isNextshop) {
                container.innerHTML = `
                <article class="ns-blog-article">
                    ${
                        data.featured_image
                            ? `<div class="ns-blog-hero"><img src="${escapeHtml(data.featured_image)}" alt=""></div>`
                            : ""
                    }
                    <header class="ns-blog-article-head">
                        <a href="/blog/" class="ns-back-link"><i data-lucide="arrow-right"></i> بازگشت به وبلاگ</a>
                        <h1 class="ns-page-title">${escapeHtml(data.title)}</h1>
                        <div class="ns-blog-article-meta">
                            <span>${formatDate(data.published_at)}</span>
                            ${data.author ? `<span>${escapeHtml(data.author)}</span>` : ""}
                            ${data.category ? `<span>${escapeHtml(data.category)}</span>` : ""}
                        </div>
                        ${tags ? `<div class="ns-blog-tags">${tags}</div>` : ""}
                    </header>
                    <div class="ns-blog-prose">${data.content || ""}</div>
                </article>`;
            } else {
                container.innerHTML = `
                <article class="card">
                    ${data.featured_image ? `<img src="${escapeHtml(data.featured_image)}" alt="" style="width:100%; max-height:400px; object-fit:cover; border-radius:var(--radius);">` : ""}
                    <h1 class="page-title">${escapeHtml(data.title)}</h1>
                    <p class="muted">${formatDate(data.published_at)}${data.author ? " — " + escapeHtml(data.author) : ""}</p>
                    <div style="margin-top:1.5rem; line-height:1.9;">${data.content || ""}</div>
                </article>`;
            }

            refreshIcons();
            const commentsSection = document.getElementById("blog-comments-section");
            if (commentsSection) {
                commentsSection.style.display = "block";
                loadComments(slug);
            }
        });
    }

    function renderComment(c) {
        const wrapClass = isPulse ? "ps-blog-comment" : "ns-blog-comment";
        const replyClass = isPulse ? "ps-blog-comment ps-blog-comment--reply" : "ns-blog-comment ns-blog-comment--reply";
        const replies = (c.replies || [])
            .map(
                (r) => `
            <div class="${replyClass}">
                <strong>${escapeHtml(r.user?.full_name || "کاربر")}</strong>
                <p>${escapeHtml(r.body)}</p>
                <time>${formatDate(r.created_at)}</time>
            </div>`
            )
            .join("");
        return `
            <div class="${wrapClass}">
                <strong>${escapeHtml(c.user?.full_name || "کاربر")}</strong>
                <p>${escapeHtml(c.body)}</p>
                <time>${formatDate(c.created_at)}</time>
                ${replies}
            </div>`;
    }

    function loadComments(slug) {
        apiFetch(`/posts/${slug}/comments`).then(({ ok, data }) => {
            const list = document.getElementById("blog-comments-list");
            if (!list || !ok) return;
            const items = Array.isArray(data) ? data : [];
            list.innerHTML = items.length
                ? items.map(renderComment).join("")
                : `<p class="${isPulse ? "ps-page-sub" : "ns-page-sub"}">اولین نظر را بنویسید.</p>`;
        });
    }

    const listPage = document.getElementById("blog-list-page");
    if (listPage) {
        loadCategories();
        loadPosts("");
    }

    const singlePage = document.getElementById("blog-single-page");
    if (singlePage) {
        const slug = singlePage.dataset.slug;
        loadSinglePost(slug);

        document.getElementById("submit-blog-comment")?.addEventListener("click", () => {
            const body = document.getElementById("blog-comment-body")?.value.trim();
            const msg = document.getElementById("blog-comment-message");
            if (!body) return;
            apiFetch(`/posts/${slug}/comments`, {
                method: "POST",
                body: JSON.stringify({ body }),
            }).then(({ ok, status, data }) => {
                if (status === 401) {
                    if (msg) msg.textContent = "برای ثبت نظر وارد شوید.";
                    return;
                }
                if (ok) {
                    if (msg) msg.textContent = "نظر ثبت شد و پس از تایید نمایش داده می‌شود.";
                    document.getElementById("blog-comment-body").value = "";
                } else if (msg) {
                    msg.textContent = (data && data.detail) || "خطا در ثبت نظر";
                }
            });
        });
    }
})();
