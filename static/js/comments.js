(function () {
    const API = "/api/v1/comments";

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

    function renderStars(rating) {
        if (!rating) return "";
        return "★".repeat(rating) + "☆".repeat(5 - rating);
    }

    function renderComment(c, options = {}) {
        const showReply = options.showReply !== false;
        const showLike = options.showLike !== false;
        const repliesHtml = (c.replies || []).map((r) => `
            <div class="card" style="margin-top:0.5rem; margin-right:1rem;">
                <strong>${r.user.full_name}</strong>
                <p>${r.body}</p>
                <p class="muted">${new Date(r.created_at).toLocaleString("fa-IR")}</p>
            </div>
        `).join("");

        return `
            <div class="card comment-card" data-comment-id="${c.id}">
                <div style="display:flex; justify-content:space-between; gap:0.5rem; flex-wrap:wrap;">
                    <div>
                        <strong>${c.user.full_name}</strong>
                        ${c.is_verified_purchase ? '<span class="status-badge">خریدار</span>' : ""}
                        ${c.rating ? `<span style="color:var(--accent);">${renderStars(c.rating)}</span>` : ""}
                    </div>
                    ${c.status_label ? `<span class="status-badge">${c.status_label}</span>` : ""}
                </div>
                <p style="margin:0.5rem 0;">${c.body}</p>
                <div class="comment-meta muted">
                    <span>${new Date(c.created_at).toLocaleString("fa-IR")}</span>
                    ${showLike ? `<button type="button" class="btn btn-outline like-comment" data-id="${c.id}">${c.liked_by_me ? "♥" : "♡"} ${c.likes_count}</button>` : ""}
                </div>
                ${repliesHtml}
                ${showReply ? `
                    <div class="reply-form" style="margin-top:0.75rem; display:none;" data-reply-for="${c.id}">
                        <textarea rows="2" style="width:100%; padding:0.5rem;" placeholder="پاسخ شما..."></textarea>
                        <button type="button" class="btn btn-outline submit-reply" data-id="${c.id}" style="margin-top:0.35rem;">ارسال پاسخ</button>
                    </div>
                    <button type="button" class="btn btn-outline toggle-reply" data-id="${c.id}" style="margin-top:0.5rem;">پاسخ</button>
                ` : ""}
            </div>
        `;
    }

    function bindCommentEvents(container, productSlug) {
        container.querySelectorAll(".like-comment").forEach((btn) => {
            btn.addEventListener("click", () => {
                apiFetch("/like", {
                    method: "POST",
                    body: JSON.stringify({ comment_id: Number(btn.dataset.id) }),
                }).then(({ ok, data }) => {
                    if (ok) {
                        btn.textContent = `${data.liked ? "♥" : "♡"} ${data.likes_count}`;
                    } else if (data.detail && window.ShopToast) {
                        window.ShopToast.error(data.detail);
                    }
                });
            });
        });

        container.querySelectorAll(".toggle-reply").forEach((btn) => {
            btn.addEventListener("click", () => {
                const form = container.querySelector(`[data-reply-for="${btn.dataset.id}"]`);
                if (form) form.style.display = form.style.display === "none" ? "block" : "none";
            });
        });

        container.querySelectorAll(".submit-reply").forEach((btn) => {
            btn.addEventListener("click", () => {
                const form = container.querySelector(`[data-reply-for="${btn.dataset.id}"]`);
                const textarea = form?.querySelector("textarea");
                if (!textarea || !textarea.value.trim()) return;
                apiFetch("/", {
                    method: "POST",
                    body: JSON.stringify({
                        product_slug: productSlug,
                        body: textarea.value.trim(),
                        parent_id: Number(btn.dataset.id),
                    }),
                }).then(({ ok, data }) => {
                    if (ok) {
                        textarea.value = "";
                        loadProductComments(productSlug);
                    } else if (window.ShopToast) {
                        window.ShopToast.error(data.detail || "خطا");
                    }
                });
            });
        });
    }

    function loadProductComments(slug) {
        const section = document.getElementById("product-comments");
        if (!section) return;

        apiFetch(`/product/${slug}`).then(({ ok, data }) => {
            const summaryEl = document.getElementById("comments-summary");
            const listEl = document.getElementById("comments-list");
            if (!ok || !listEl) return;

            if (summaryEl) {
                summaryEl.textContent = data.summary.review_count
                    ? `${data.summary.average_rating} از ۵ — ${data.summary.review_count} نظر`
                    : "هنوز نظری ثبت نشده";
            }

            if (!data.items.length) {
                listEl.innerHTML = '<div class="empty-state card">اولین نظر را ثبت کنید.</div>';
            } else {
                listEl.innerHTML = data.items.map((c) => renderComment(c)).join("");
                bindCommentEvents(listEl, slug);
            }
        });
    }

    function loadMyComments() {
        const list = document.getElementById("my-comments-list");
        if (!list) return;

        apiFetch("/mine").then(({ ok, status, data }) => {
            if (status === 401) {
                list.innerHTML =
                    '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="log-in"></i></div>' +
                    "<strong>ورود لازم است</strong><p>برای مشاهده نظرات وارد شوید.</p>" +
                    '<a class="ns-btn" href="/login/?next=/comments/">ورود</a></div>';
                if (window.lucide) window.lucide.createIcons();
                return;
            }
            if (!ok || !data.length) {
                list.innerHTML =
                    '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="message-square"></i></div>' +
                    "<strong>هنوز نظری ثبت نکرده‌اید</strong><p>پس از خرید می‌توانید تجربه خود را بنویسید.</p>" +
                    '<a class="ns-btn ns-btn--ghost" href="/products/">مشاهده محصولات</a></div>';
                if (window.lucide) window.lucide.createIcons();
                return;
            }
            list.innerHTML = data.map((c) => renderComment(c, { showReply: false, showLike: false })).join("");
        });
    }

    const productSection = document.getElementById("product-comments");
    if (productSection) {
        const slug = productSection.dataset.product;
        loadProductComments(slug);

        document.getElementById("submit-review")?.addEventListener("click", () => {
            const body = document.getElementById("review-body")?.value.trim();
            const rating = Number(document.getElementById("review-rating")?.value || 0);
            const msg = document.getElementById("review-message");
            if (!body) return;
            apiFetch("/", {
                method: "POST",
                body: JSON.stringify({ product_slug: slug, body, rating: rating || null }),
            }).then(({ ok, data }) => {
                if (ok) {
                    if (msg) msg.textContent = "نظر شما ثبت شد و پس از تایید نمایش داده می‌شود.";
                    document.getElementById("review-body").value = "";
                    loadMyComments();
                } else if (msg) {
                    msg.textContent = data.detail || "خطا";
                }
            });
        });
    }

    if (document.getElementById("my-comments-page")) {
        loadMyComments();
    }

    window.ShopComments = { loadProductComments, loadMyComments };
})();
