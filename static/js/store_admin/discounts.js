(function () {
    const root = document.getElementById("sa-discounts");
    if (!root || !window.StoreAdminApi) return;
    const api = window.StoreAdminApi;
    if (!api.requireAuth("/manage/discounts/")) return;

    const couponWrap = document.getElementById("coupon-table-wrap");
    const giftWrap = document.getElementById("gift-table-wrap");
    const couponDialog = document.getElementById("coupon-dialog");
    const giftDialog = document.getElementById("gift-dialog");
    const couponForm = document.getElementById("coupon-form");
    const giftForm = document.getElementById("gift-form");

    let coupons = [];
    let gifts = [];

    function typeLabel(type) {
        return type === "fixed" ? "مبلغ ثابت" : "درصدی";
    }

    function scopeLabel(scope) {
        if (scope === "category") return "دسته‌بندی";
        if (scope === "product") return "محصول";
        return "همه";
    }

    function formatDate(iso) {
        if (!iso) return "—";
        try {
            return new Date(iso).toLocaleString("fa-IR");
        } catch (_) {
            return iso;
        }
    }

    function toLocalInput(iso) {
        if (!iso) return "";
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return "";
        const pad = function (n) {
            return String(n).padStart(2, "0");
        };
        return (
            d.getFullYear() +
            "-" +
            pad(d.getMonth() + 1) +
            "-" +
            pad(d.getDate()) +
            "T" +
            pad(d.getHours()) +
            ":" +
            pad(d.getMinutes())
        );
    }

    function optionalNumber(id) {
        const raw = (document.getElementById(id).value || "").trim();
        if (!raw) return null;
        const n = Number(raw);
        return Number.isFinite(n) ? n : null;
    }

    function optionalDate(id) {
        const raw = (document.getElementById(id).value || "").trim();
        return raw || null;
    }

    function activeBadge(active) {
        return active
            ? '<span class="sa-badge sa-badge-ok">فعال</span>'
            : '<span class="sa-badge sa-badge-muted">غیرفعال</span>';
    }

    function renderCoupons() {
        if (!coupons.length) {
            couponWrap.innerHTML = '<div class="sa-empty">هنوز کد تخفیفی ساخته نشده است.</div>';
            return;
        }
        couponWrap.innerHTML =
            '<div class="sa-table-wrap"><table class="sa-table"><thead><tr>' +
            "<th>کد</th><th>نوع</th><th>مقدار</th><th>محدوده</th><th>استفاده</th><th>اعتبار</th><th>وضعیت</th><th></th>" +
            "</tr></thead><tbody>" +
            coupons
                .map(function (c) {
                    const uses =
                        (c.used_count || 0) +
                        (c.max_uses != null ? " / " + c.max_uses : "");
                    return (
                        "<tr>" +
                        '<td dir="ltr"><strong>' +
                        api.escapeHtml(c.code) +
                        "</strong></td>" +
                        "<td>" +
                        typeLabel(c.discount_type) +
                        "</td>" +
                        "<td>" +
                        api.formatNumber(c.value) +
                        (c.discount_type === "percentage" ? "٪" : "") +
                        "</td>" +
                        "<td>" +
                        scopeLabel(c.scope) +
                        "</td>" +
                        "<td>" +
                        uses +
                        "</td>" +
                        "<td>" +
                        formatDate(c.valid_until) +
                        "</td>" +
                        "<td>" +
                        activeBadge(c.is_active) +
                        "</td>" +
                        '<td class="sa-row-actions">' +
                        '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm js-coupon-edit" data-id="' +
                        c.id +
                        '">ویرایش</button> ' +
                        '<button type="button" class="sa-btn sa-btn-danger sa-btn-sm js-coupon-del" data-id="' +
                        c.id +
                        '">حذف</button>' +
                        "</td></tr>"
                    );
                })
                .join("") +
            "</tbody></table></div>";
    }

    function renderGifts() {
        if (!gifts.length) {
            giftWrap.innerHTML = '<div class="sa-empty">هنوز کارت هدیه‌ای ساخته نشده است.</div>';
            return;
        }
        giftWrap.innerHTML =
            '<div class="sa-table-wrap"><table class="sa-table"><thead><tr>' +
            "<th>کد</th><th>موجودی</th><th>اولیه</th><th>اعتبار</th><th>وضعیت</th><th></th>" +
            "</tr></thead><tbody>" +
            gifts
                .map(function (g) {
                    return (
                        "<tr>" +
                        '<td dir="ltr"><strong>' +
                        api.escapeHtml(g.code) +
                        "</strong></td>" +
                        "<td>" +
                        api.formatNumber(g.balance) +
                        "</td>" +
                        "<td>" +
                        api.formatNumber(g.initial_balance) +
                        "</td>" +
                        "<td>" +
                        formatDate(g.valid_until) +
                        "</td>" +
                        "<td>" +
                        activeBadge(g.is_active) +
                        "</td>" +
                        '<td class="sa-row-actions">' +
                        '<button type="button" class="sa-btn sa-btn-ghost sa-btn-sm js-gift-edit" data-id="' +
                        g.id +
                        '">ویرایش</button> ' +
                        '<button type="button" class="sa-btn sa-btn-danger sa-btn-sm js-gift-del" data-id="' +
                        g.id +
                        '">حذف</button>' +
                        "</td></tr>"
                    );
                })
                .join("") +
            "</tbody></table></div>";
    }

    function load() {
        api.setPageLoading(couponWrap, true);
        api.setPageLoading(giftWrap, true);
        return Promise.all([
            api.apiFetch("/api/v1/store-admin/discounts/coupons"),
            api.apiFetch("/api/v1/store-admin/discounts/gift-cards"),
        ]).then(function (results) {
            api.setPageLoading(couponWrap, false);
            api.setPageLoading(giftWrap, false);
            const couponRes = results[0];
            const giftRes = results[1];
            if (!couponRes.ok) {
                couponWrap.innerHTML = '<div class="sa-empty">خطا در بارگذاری کدهای تخفیف.</div>';
            } else {
                coupons = api.unwrapList(couponRes.data);
                renderCoupons();
            }
            if (!giftRes.ok) {
                giftWrap.innerHTML = '<div class="sa-empty">خطا در بارگذاری کارت‌های هدیه.</div>';
            } else {
                gifts = api.unwrapList(giftRes.data);
                renderGifts();
            }
        });
    }

    function openCoupon(item) {
        document.getElementById("coupon-dialog-title").textContent = item ? "ویرایش کد تخفیف" : "کد تخفیف جدید";
        document.getElementById("coupon-id").value = item ? item.id : "";
        document.getElementById("coupon-code").value = item ? item.code : "";
        document.getElementById("coupon-type").value = item ? item.discount_type : "percentage";
        document.getElementById("coupon-value").value = item ? item.value : "";
        document.getElementById("coupon-scope").value = item ? item.scope : "all";
        document.getElementById("coupon-min-order").value = item ? item.min_order_amount || 0 : 0;
        document.getElementById("coupon-max-discount").value = item && item.max_discount_amount ? item.max_discount_amount : "";
        document.getElementById("coupon-max-uses").value = item && item.max_uses != null ? item.max_uses : "";
        document.getElementById("coupon-per-user").value = item && item.per_user_limit != null ? item.per_user_limit : "";
        document.getElementById("coupon-valid-from").value = item ? toLocalInput(item.valid_from) : "";
        document.getElementById("coupon-valid-until").value = item ? toLocalInput(item.valid_until) : "";
        document.getElementById("coupon-active").checked = item ? !!item.is_active : true;
        document.getElementById("coupon-first-purchase").checked = item ? !!item.first_purchase_only : false;
        couponDialog.showModal();
    }

    function openGift(item) {
        document.getElementById("gift-dialog-title").textContent = item ? "ویرایش کارت هدیه" : "کارت هدیه جدید";
        document.getElementById("gift-id").value = item ? item.id : "";
        document.getElementById("gift-code").value = item ? item.code : "";
        document.getElementById("gift-code").disabled = !!item;
        document.getElementById("gift-initial").value = item ? item.initial_balance : "";
        document.getElementById("gift-balance").value = item ? item.balance : "";
        document.getElementById("gift-initial-wrap").hidden = !!item;
        document.getElementById("gift-balance-wrap").hidden = !item;
        document.getElementById("gift-initial").required = !item;
        document.getElementById("gift-valid-until").value = item ? toLocalInput(item.valid_until) : "";
        document.getElementById("gift-active").checked = item ? !!item.is_active : true;
        giftDialog.showModal();
    }

    couponWrap.addEventListener("click", function (e) {
        const editBtn = e.target.closest(".js-coupon-edit");
        const delBtn = e.target.closest(".js-coupon-del");
        if (editBtn) {
            const item = coupons.find(function (c) {
                return String(c.id) === editBtn.getAttribute("data-id");
            });
            if (item) openCoupon(item);
        }
        if (delBtn) {
            if (!window.confirm("این کد تخفیف حذف شود؟")) return;
            api.setBusy(delBtn, true, "حذف...");
            api.apiFetch("/api/v1/store-admin/discounts/coupons/" + delBtn.getAttribute("data-id"), {
                method: "DELETE",
            }).then(function (res) {
                if (!res.ok) {
                    api.flash((res.data && res.data.detail) || "حذف انجام نشد", true);
                    api.setBusy(delBtn, false);
                    return;
                }
                api.flash("کد تخفیف حذف شد.");
                load();
            });
        }
    });

    giftWrap.addEventListener("click", function (e) {
        const editBtn = e.target.closest(".js-gift-edit");
        const delBtn = e.target.closest(".js-gift-del");
        if (editBtn) {
            const item = gifts.find(function (g) {
                return String(g.id) === editBtn.getAttribute("data-id");
            });
            if (item) openGift(item);
        }
        if (delBtn) {
            if (!window.confirm("این کارت هدیه حذف شود؟")) return;
            api.setBusy(delBtn, true, "حذف...");
            api.apiFetch("/api/v1/store-admin/discounts/gift-cards/" + delBtn.getAttribute("data-id"), {
                method: "DELETE",
            }).then(function (res) {
                if (!res.ok) {
                    api.flash((res.data && res.data.detail) || "حذف انجام نشد", true);
                    api.setBusy(delBtn, false);
                    return;
                }
                api.flash("کارت هدیه حذف شد.");
                load();
            });
        }
    });

    document.getElementById("coupon-new").addEventListener("click", function () {
        openCoupon(null);
    });
    document.getElementById("gift-new").addEventListener("click", function () {
        openGift(null);
    });
    document.getElementById("coupon-cancel").addEventListener("click", function () {
        couponDialog.close();
    });
    document.getElementById("gift-cancel").addEventListener("click", function () {
        giftDialog.close();
    });

    couponForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const id = document.getElementById("coupon-id").value;
        const payload = {
            code: document.getElementById("coupon-code").value,
            discount_type: document.getElementById("coupon-type").value,
            value: Number(document.getElementById("coupon-value").value),
            scope: document.getElementById("coupon-scope").value,
            min_order_amount: Number(document.getElementById("coupon-min-order").value || 0),
            max_discount_amount: optionalNumber("coupon-max-discount"),
            max_uses: optionalNumber("coupon-max-uses"),
            per_user_limit: optionalNumber("coupon-per-user"),
            valid_from: optionalDate("coupon-valid-from"),
            valid_until: optionalDate("coupon-valid-until"),
            is_active: document.getElementById("coupon-active").checked,
            first_purchase_only: document.getElementById("coupon-first-purchase").checked,
        };
        const path = id
            ? "/api/v1/store-admin/discounts/coupons/" + id
            : "/api/v1/store-admin/discounts/coupons";
        api.apiFetch(path, {
            method: id ? "PUT" : "POST",
            body: JSON.stringify(payload),
        }).then(function (res) {
            if (!res.ok) {
                api.flash((res.data && res.data.detail) || "ذخیره انجام نشد", true);
                return;
            }
            couponDialog.close();
            api.flash(id ? "کد تخفیف به‌روز شد." : "کد تخفیف ساخته شد.");
            load();
        });
    });

    giftForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const id = document.getElementById("gift-id").value;
        const payload = {
            is_active: document.getElementById("gift-active").checked,
            valid_until: optionalDate("gift-valid-until"),
        };
        let path = "/api/v1/store-admin/discounts/gift-cards";
        let method = "POST";
        if (id) {
            path = path + "/" + id;
            method = "PUT";
            payload.balance = Number(document.getElementById("gift-balance").value || 0);
        } else {
            payload.code = document.getElementById("gift-code").value;
            payload.initial_balance = Number(document.getElementById("gift-initial").value || 0);
        }
        api.apiFetch(path, {
            method: method,
            body: JSON.stringify(payload),
        }).then(function (res) {
            if (!res.ok) {
                api.flash((res.data && res.data.detail) || "ذخیره انجام نشد", true);
                return;
            }
            giftDialog.close();
            api.flash(id ? "کارت هدیه به‌روز شد." : "کارت هدیه ساخته شد.");
            load();
        });
    });

    load();
})();
