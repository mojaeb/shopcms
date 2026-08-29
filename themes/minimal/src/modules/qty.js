function formatQty(value) {
  if (window.ShopMoney) return window.ShopMoney.formatAmount(value);
  return String(value);
}

export function initQty(root = document) {
  root.querySelectorAll("[data-em-qty]").forEach((wrap) => {
    if (wrap.hasAttribute("data-em-variant-qty") || wrap.closest("[data-em-variants]")) return;
    if (wrap.dataset.bound === "1") return;
    wrap.dataset.bound = "1";

    const valueEl = wrap.querySelector("[data-em-qty-value]");
    const cartBtn = wrap.closest("[data-em-product-actions]")?.querySelector("[data-add-to-cart]");
    let qty = Math.max(1, Number(wrap.dataset.qty) || 1);

    const sync = () => {
      wrap.dataset.qty = String(qty);
      if (valueEl) valueEl.textContent = formatQty(qty);
      if (cartBtn) cartBtn.dataset.quantity = String(qty);
    };

    wrap.addEventListener("click", (event) => {
      if (event.target.closest("[data-em-qty-inc]")) {
        qty += 1;
        sync();
        return;
      }
      if (event.target.closest("[data-em-qty-dec]")) {
        qty = Math.max(1, qty - 1);
        sync();
      }
    });

    sync();
  });
}
