export function initQty(root = document) {
  root.querySelectorAll("[data-ps-qty]").forEach((wrap) => {
    // Variable products manage qty via variants.js
    if (wrap.hasAttribute("data-ps-variant-qty") || wrap.closest("[data-ps-variants]")) return;
    if (wrap.dataset.bound === "1") return;
    wrap.dataset.bound = "1";

    const valueEl = wrap.querySelector("[data-ps-qty-value]");
    const dec = wrap.querySelector("[data-ps-qty-dec]");
    const inc = wrap.querySelector("[data-ps-qty-inc]");
    const cartBtn = wrap.closest("[data-ps-product-actions]")?.querySelector("[data-add-to-cart]");
    let qty = Number(String(valueEl?.textContent || "1").replace(/[^\d]/g, "")) || 1;

    const sync = () => {
      if (valueEl) {
        valueEl.textContent = window.ShopMoney
          ? window.ShopMoney.formatAmount(qty)
          : String(qty);
      }
      if (cartBtn) cartBtn.dataset.quantity = String(qty);
    };

    dec?.addEventListener("click", () => {
      qty = Math.max(1, qty - 1);
      sync();
    });
    inc?.addEventListener("click", () => {
      qty += 1;
      sync();
    });
    sync();
  });
}
