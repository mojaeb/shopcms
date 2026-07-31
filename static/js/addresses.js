(function () {
    const root = document.getElementById("addresses-page");
    if (!root) return;

    const API = "/api/v1/addresses";

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

    function formData(form) {
        const data = Object.fromEntries(new FormData(form).entries());
        data.is_default = form.querySelector('[name="is_default"]')?.checked || false;
        return data;
    }

    function renderAddressCard(address) {
        return `
            <div class="card address-card" data-id="${address.id}">
                <div style="display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap;">
                    <div>
                        <h3>${address.full_name} ${address.is_default ? '<span class="badge">پیش‌فرض</span>' : ""}</h3>
                        <p class="muted">${address.phone}</p>
                        <p>${address.full_address}</p>
                        <p class="muted">کد پستی: ${address.postal_code}</p>
                    </div>
                    <div style="display:flex; gap:0.5rem; flex-wrap:wrap; align-items:flex-start;">
                        ${!address.is_default ? `<button type="button" class="btn btn-outline set-default" data-id="${address.id}">پیش‌فرض</button>` : ""}
                        <button type="button" class="btn btn-outline edit-address" data-id="${address.id}">ویرایش</button>
                        <button type="button" class="btn btn-outline delete-address" data-id="${address.id}">حذف</button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderList(addresses) {
        const list = document.getElementById("address-list");
        if (!list) return;
        if (!addresses.length) {
            list.innerHTML =
                '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="map-pin"></i></div>' +
                "<strong>آدرسی ثبت نشده</strong><p>یک آدرس تحویل اضافه کنید تا تسویه سریع‌تر انجام شود.</p></div>";
            if (window.lucide) window.lucide.createIcons();
            return;
        }
        list.innerHTML = addresses.map(renderAddressCard).join("");
        bindListEvents();
    }

    function bindListEvents() {
        document.querySelectorAll(".set-default").forEach((btn) => {
            btn.addEventListener("click", () => {
                apiFetch(`/${btn.dataset.id}/set-default`, { method: "POST", body: "{}" }).then(loadAddresses);
            });
        });
        document.querySelectorAll(".delete-address").forEach((btn) => {
            btn.addEventListener("click", () => {
                if (!confirm("آدرس حذف شود؟")) return;
                apiFetch(`/${btn.dataset.id}`, { method: "DELETE" }).then(loadAddresses);
            });
        });
        document.querySelectorAll(".edit-address").forEach((btn) => {
            btn.addEventListener("click", () => openForm(Number(btn.dataset.id)));
        });
    }

    function openForm(addressId) {
        const panel = document.getElementById("address-form-panel");
        const form = document.getElementById("address-form");
        if (!panel || !form) return;
        panel.style.display = "block";
        form.reset();
        form.dataset.id = addressId || "";
        document.getElementById("form-title").textContent = addressId ? "ویرایش آدرس" : "افزودن آدرس";
        if (addressId) {
            apiFetch(`/${addressId}`).then(({ ok, data }) => {
                if (!ok) return;
                Object.keys(data).forEach((key) => {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (!input) return;
                    if (input.type === "checkbox") input.checked = !!data[key];
                    else input.value = data[key] || "";
                });
            });
        }
    }

    function closeForm() {
        const panel = document.getElementById("address-form-panel");
        if (panel) panel.style.display = "none";
    }

    function loadAddresses() {
        apiFetch("/").then(({ ok, status, data }) => {
            if (status === 401) {
                document.getElementById("address-list").innerHTML =
                    '<div class="ns-empty"><div class="ns-empty-icon" aria-hidden="true"><i data-lucide="log-in"></i></div>' +
                    "<strong>ورود لازم است</strong><p>برای مدیریت آدرس‌ها وارد شوید.</p>" +
                    '<a class="ns-btn" href="/login/?next=/addresses/">ورود</a></div>';
                if (window.lucide) window.lucide.createIcons();
                return;
            }
            if (ok) renderList(data);
        });
    }

    document.getElementById("add-address-btn")?.addEventListener("click", () => openForm(null));
    document.getElementById("cancel-address-btn")?.addEventListener("click", closeForm);

    document.getElementById("address-form")?.addEventListener("submit", (e) => {
        e.preventDefault();
        const form = e.target;
        const payload = formData(form);
        const id = form.dataset.id;
        const method = id ? "PUT" : "POST";
        const path = id ? `/${id}` : "/";
        apiFetch(path, { method, body: JSON.stringify(payload) }).then(({ ok, data }) => {
            const msg = document.getElementById("form-message");
            if (ok) {
                if (msg) msg.textContent = "";
                closeForm();
                loadAddresses();
            } else if (msg) {
                msg.textContent = data.detail || "خطا در ذخیره آدرس";
            }
        });
    });

    loadAddresses();
})();
