(function () {
    const API = "/api/v1/blog";

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

    function formatDate(iso) {
        if (!iso) return "";
        return new Date(iso).toLocaleDateString("fa-IR");
    }

    function renderPostCard(post) {
        return `
            <a href="/blog/${post.slug}/" class="card blog-card">
                ${post.featured_image ? `<img src="${post.featured_image}" alt="">` : ""}
                <h3 style="margin-top:0.75rem;">${post.title}</h3>
                <p class="muted">${post.excerpt || ""}</p>
                <p class="muted">${formatDate(post.published_at)}${post.category ? " — " + post.category : ""}</p>
            </a>
        `;
    }

    function loadCategories() {
        const el = document.getElementById("blog-categories");
        if (!el) return;
        apiFetch("/categories").then(({ ok, data }) => {
            if (!ok) return;
            el.innerHTML = `<button type="button" class="btn btn-outline blog-filter" data-category="">همه</button>` +
                data.map((c) => `<button type="button" class="btn btn-outline blog-filter" data-category="${c.slug}">${c.name}</button>`).join("");
            el.querySelectorAll(".blog-filter").forEach((btn) => {
                btn.addEventListener("click", () => loadPosts(btn.dataset.category));
            });
        });
    }

    function loadPosts(category) {
        const container = document.getElementById("blog-posts");
        if (!container) return;
        const qs = category ? `?category=${encodeURIComponent(category)}` : "";
        apiFetch(`/posts${qs}`).then(({ ok, data }) => {
            if (!ok) {
                container.innerHTML = '<div class="empty-state card">وبلاگ فعال نیست.</div>';
                return;
            }
            const items = data.items || data;
            if (!items.length) {
                container.innerHTML = '<div class="empty-state card">مطلبی یافت نشد.</div>';
                return;
            }
            container.innerHTML = `<div class="blog-grid">${items.map(renderPostCard).join("")}</div>`;
        });
    }

    function loadSinglePost(slug) {
        const container = document.getElementById("blog-post-content");
        if (!container) return;

        apiFetch(`/posts/${slug}`).then(({ ok, data }) => {
            if (!ok) {
                container.innerHTML = '<div class="empty-state card">مقاله یافت نشد.</div>';
                return;
            }
            document.title = (data.seo?.meta_title || data.title) + " - وبلاگ";
            container.innerHTML = `
                <article class="card">
                    ${data.featured_image ? `<img src="${data.featured_image}" alt="" style="width:100%; max-height:400px; object-fit:cover; border-radius:var(--radius);">` : ""}
                    <h1 class="page-title">${data.title}</h1>
                    <p class="muted">${formatDate(data.published_at)}${data.author ? " — " + data.author : ""}</p>
                    ${data.tags?.length ? `<p class="muted">${data.tags.map((t) => t.name).join("، ")}</p>` : ""}
                    <div style="margin-top:1.5rem; line-height:1.9;">${data.content}</div>
                </article>
            `;
            const commentsSection = document.getElementById("blog-comments-section");
            if (commentsSection) {
                commentsSection.style.display = "block";
                loadComments(slug);
            }
        });
    }

    function renderComment(c) {
        const replies = (c.replies || []).map((r) => `
            <div class="card" style="margin-top:0.5rem; margin-right:1rem;">
                <strong>${r.user.full_name}</strong>
                <p>${r.body}</p>
                <p class="muted">${formatDate(r.created_at)}</p>
            </div>
        `).join("");
        return `
            <div class="card" style="margin-bottom:0.75rem;">
                <strong>${c.user.full_name}</strong>
                <p>${c.body}</p>
                <p class="muted">${formatDate(c.created_at)}</p>
                ${replies}
            </div>
        `;
    }

    function loadComments(slug) {
        apiFetch(`/posts/${slug}/comments`).then(({ ok, data }) => {
            const list = document.getElementById("blog-comments-list");
            if (!list || !ok) return;
            list.innerHTML = data.length ? data.map(renderComment).join("") : '<p class="muted">اولین نظر را بنویسید.</p>';
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
                    msg.textContent = data.detail || "خطا";
                }
            });
        });
    }
})();
