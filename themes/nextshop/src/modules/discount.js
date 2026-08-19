/**
 * Discount panel: tab switching (coupon ↔ gift card)
 * and decorating the #coupon-message element with success/error classes.
 */
export function initDiscountTabs() {
  const tabs = document.querySelectorAll(".ns-discount-tab[data-tab]");
  if (!tabs.length) return;

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.dataset.tab;
      tabs.forEach((t) => {
        const active = t.dataset.tab === target;
        t.classList.toggle("ns-discount-tab--active", active);
        t.setAttribute("aria-selected", active ? "true" : "false");
      });
      document.querySelectorAll(".ns-discount-panel[data-panel]").forEach((panel) => {
        panel.hidden = panel.dataset.panel !== target;
      });
      const input = document.querySelector(
        `.ns-discount-panel[data-panel="${target}"] .ns-discount-input`
      );
      if (input) input.focus();
    });
  });

  // Decorate coupon-message with success/error classes based on cart.js behaviour.
  // cart.js sets msg.textContent after apply/remove — we observe that.
  const msg = document.getElementById("coupon-message");
  if (!msg) return;

  const SUCCESS_TEXTS = ["اعمال شد", "کوپن اعمال شد", "کارت هدیه اعمال شد"];

  const observer = new MutationObserver(() => {
    const text = msg.textContent.trim();
    if (!text) {
      msg.classList.remove("is-success", "is-error");
      return;
    }
    const isSuccess = SUCCESS_TEXTS.some((s) => text.includes(s.replace("اعمال شد", "")));
    // Heuristic: if the message contains "نامعتبر", "یافت نشد", "خطا" it's an error
    const isError = /نامعتبر|یافت نشد|خطا|ناموجود/.test(text);
    msg.classList.toggle("is-success", isSuccess && !isError);
    msg.classList.toggle("is-error", isError);
  });

  observer.observe(msg, { childList: true, characterData: true, subtree: true });

  // Show/hide remove buttons after apply events via intercepting the apply buttons
  wireRemoveVisibility("apply-coupon", "remove-coupon");
  wireRemoveVisibility("apply-gift", "remove-gift");
}

function wireRemoveVisibility(applyId, removeId) {
  const applyBtn = document.getElementById(applyId);
  const removeBtn = document.getElementById(removeId);
  if (!applyBtn || !removeBtn) return;

  // When apply succeeds, cart.js calls notifyCartUpdated which triggers a custom event
  // We piggyback on coupon-message mutation to decide visibility
  const msg = document.getElementById("coupon-message");
  if (!msg) return;

  const SUCCESS_KEYWORD = applyId === "apply-coupon" ? "کوپن" : "کارت هدیه";

  new MutationObserver(() => {
    const text = msg.textContent.trim();
    if (text.includes(SUCCESS_KEYWORD) && text.includes("اعمال شد")) {
      removeBtn.hidden = false;
    }
  }).observe(msg, { childList: true, characterData: true, subtree: true });

  removeBtn.addEventListener("click", () => {
    removeBtn.hidden = true;
    const input = document.getElementById(
      applyId === "apply-coupon" ? "coupon-code" : "gift-code"
    );
    if (input) input.value = "";
  });
}
