/**
 * Product quantity stepper. Uses event delegation so Lucide SVG
 * swaps inside the buttons cannot drop the click handler.
 */
export function initQty(root = document) {
  root.querySelectorAll("[data-ns-qty]").forEach((wrap) => {
    if (wrap.dataset.bound === "1") return;
    wrap.dataset.bound = "1";

    const valueEl = wrap.querySelector("[data-ns-qty-value]");
    const actions = wrap.closest(".ns-product-actions");
    const cartBtn = actions?.querySelector("[data-add-to-cart]");
    const alpineHost = wrap.closest("[x-data]");

    let qty = Math.max(1, Number(wrap.dataset.qty) || 1);

    const alpineState = () => {
      if (alpineHost && alpineHost._x_dataStack && alpineHost._x_dataStack.length) {
        return alpineHost._x_dataStack[0];
      }
      return null;
    };

    const sync = () => {
      wrap.dataset.qty = String(qty);
      if (valueEl) {
        valueEl.textContent = window.ShopMoney
          ? window.ShopMoney.formatAmount(qty)
          : String(qty);
      }
      if (cartBtn) cartBtn.dataset.quantity = String(qty);
      const state = alpineState();
      if (state && Object.prototype.hasOwnProperty.call(state, "qty")) {
        state.qty = qty;
      }
    };

    wrap.addEventListener("click", (event) => {
      if (event.target.closest("[data-ns-qty-inc]")) {
        qty += 1;
        sync();
        return;
      }
      if (event.target.closest("[data-ns-qty-dec]")) {
        qty = Math.max(1, qty - 1);
        sync();
      }
    });

    sync();
  });
}
