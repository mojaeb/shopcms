/**
 * Vanilla multi-variant selector for Pulse product pages.
 * Mirrors NextShop vgProductVariants selection / findVariant logic,
 * but always keeps every attribute value visible (incompatible = disabled style,
 * still clickable so the shopper can switch paths).
 */
export function initVariants(root = document) {
  root.querySelectorAll("[data-ps-variants]").forEach((host) => {
    if (host.dataset.bound === "1") return;
    host.dataset.bound = "1";
    bindVariantHost(host);
  });
}

function parseJsonScript(id, scope = document) {
  let el = null;
  if (scope && scope.querySelector) {
    try {
      const safe =
        typeof CSS !== "undefined" && CSS.escape ? CSS.escape(id) : id.replace(/"/g, "");
      el = scope.querySelector(`#${safe}`);
    } catch (_e) {
      el = null;
    }
  }
  if (!el) el = document.getElementById(id);
  if (!el) return [];
  try {
    return JSON.parse(el.textContent || "[]") || [];
  } catch (_e) {
    return [];
  }
}

function formatPrice(amount) {
  if (window.ShopMoney) return window.ShopMoney.formatMoney(amount, "IRR");
  const n = Number(amount) || 0;
  return n.toLocaleString("fa-IR") + " تومان";
}

function bindVariantHost(host) {
  const variants = parseJsonScript("ps-product-variants", host);
  const attributeOptions = parseJsonScript("ps-product-attribute-options", host);
  const basePrice = host.dataset.basePrice || "0";
  const baseCompare = host.dataset.baseComparePrice || "";

  const state = {
    variants,
    attributeOptions,
    selected: {},
    selectedVariant: null,
    qty: 1,
    basePrice,
    baseComparePrice: baseCompare,
  };

  const priceEl = host.querySelector("[data-ps-variant-price]");
  const compareEl = host.querySelector("[data-ps-variant-compare]");
  const groupsEl = host.querySelector("[data-ps-variant-groups]");
  const summaryEl = host.querySelector("[data-ps-variant-summary]");
  const cartBtn = host.querySelector("[data-add-to-cart]");
  const cartLabel = cartBtn?.querySelector("[data-ps-cart-label]");
  const qtyVal = host.querySelector("[data-ps-qty-value]");

  function variantMatchesSelection(variant, selection, strictAttrId) {
    const byAttr = {};
    (variant.attributes || []).forEach((a) => {
      byAttr[String(a.attribute_id)] = a.id;
    });
    if (strictAttrId !== undefined && strictAttrId !== null) {
      if (byAttr[String(strictAttrId)] === undefined) return false;
    }
    for (const attrId of Object.keys(selection)) {
      const chosen = Number(selection[attrId]);
      if (Number.isNaN(chosen) || !chosen) continue;
      const key = String(attrId);
      if (byAttr[key] === undefined) {
        if (Number(attrId) === Number(strictAttrId)) return false;
        continue;
      }
      if (Number(byAttr[key]) !== chosen) return false;
    }
    return true;
  }

  /** True if some variant has this value together with the *other* current selections. */
  function isValueCompatible(attrId, valueId) {
    const trial = { ...state.selected, [attrId]: valueId };
    return state.variants.some((variant) =>
      variantMatchesSelection(variant, trial, attrId)
    );
  }

  function isValueInStock(attrId, valueId) {
    const trial = { ...state.selected, [attrId]: valueId };
    return state.variants.some(
      (variant) =>
        variant.in_stock && variantMatchesSelection(variant, trial, attrId)
    );
  }

  /** Always expose every configured value — never hide “other” variants. */
  function getAllValues(attrId) {
    const attr = state.attributeOptions.find((a) => Number(a.id) === Number(attrId));
    return attr ? attr.values || [] : [];
  }

  function visibleAttributes() {
    return state.attributeOptions.filter((attr) => getAllValues(attr.id).length > 0);
  }

  function findVariant() {
    const selectedEntries = Object.keys(state.selected)
      .map((k) => ({ attrId: Number(k), valueId: Number(state.selected[k]) }))
      .filter((row) => row.attrId && row.valueId);
    if (!selectedEntries.length) return null;

    const requiredAttrIds = visibleAttributes().map((a) => Number(a.id));
    const selectedAttrIds = selectedEntries.map((r) => r.attrId);
    for (let i = 0; i < requiredAttrIds.length; i++) {
      if (selectedAttrIds.indexOf(requiredAttrIds[i]) === -1) return null;
    }

    return (
      state.variants.find((variant) =>
        variantMatchesSelection(variant, state.selected, null)
      ) || null
    );
  }

  function selectedLabel(attrId) {
    const attr = state.attributeOptions.find((a) => Number(a.id) === Number(attrId));
    if (!attr) return "";
    const selectedId = Number(state.selected[attrId]);
    const val = (attr.values || []).find((v) => Number(v.id) === selectedId);
    return val ? val.value : "";
  }

  function isColor(attr) {
    return (attr.display_type || "").toLowerCase() === "color";
  }

  function isList(attr) {
    const t = (attr.display_type || "").toLowerCase();
    return t === "select" || t === "list" || t === "dropdown";
  }

  function colorCodes(val) {
    if (Array.isArray(val.color_codes) && val.color_codes.length) return val.color_codes;
    if (val.color_code) {
      return String(val.color_code)
        .split(/[,،/\s]+/)
        .map((p) => p.trim())
        .filter(Boolean)
        .map((p) => (p.charAt(0) === "#" ? p : `#${p}`));
    }
    return [];
  }

  function swatchStyle(val) {
    const codes = colorCodes(val);
    if (!codes.length) return "background-color:#e2e8f0";
    if (codes.length === 1) return `background-color:${codes[0]}`;
    return `background-color:${codes[0]};background-image:linear-gradient(135deg, ${codes[0]} 50%, ${codes[1]} 50%)`;
  }

  function applyVariant(variant) {
    if (!variant) return;
    const sel = {};
    (variant.attributes || []).forEach((attr) => {
      sel[attr.attribute_id] = attr.id;
    });
    state.selected = sel;
    state.selectedVariant = variant;
  }

  /**
   * After clearing incompatible dims on an incomplete matrix (e.g. 3 of 4
   * color×warranty combos), fill any missing attributes with a compatible
   * value so a real variant/price is always resolved when possible.
   */
  function autofillMissingAttributes() {
    visibleAttributes().forEach((attr) => {
      if (state.selected[attr.id]) return;
      const values = getAllValues(attr.id);
      const pick =
        values.find((v) => isValueCompatible(attr.id, v.id) && isValueInStock(attr.id, v.id)) ||
        values.find((v) => isValueCompatible(attr.id, v.id));
      if (pick) state.selected[attr.id] = pick.id;
    });
  }

  function selectValue(attrId, valueId) {
    // Always accept the click — clear conflicting dimensions instead of no-oping
    // (hiding/blocking other options was the “بقیه variant ها نشون نمیده” failure mode).
    state.selected[attrId] = valueId;
    state.attributeOptions.forEach((attr) => {
      if (Number(attr.id) === Number(attrId)) return;
      const sel = state.selected[attr.id];
      if (!sel) return;
      if (!isValueCompatible(attr.id, sel)) delete state.selected[attr.id];
    });
    // Incomplete matrices: cleared dims leave a partial selection — auto-complete
    // onto an existing combo (never invent missing SKUs).
    if (!findVariant()) autofillMissingAttributes();
    state.selectedVariant = findVariant();
    render();
  }

  function canAddToCart() {
    return !!(state.selectedVariant && state.selectedVariant.in_stock);
  }

  function displayPrice() {
    return state.selectedVariant ? state.selectedVariant.price : state.basePrice;
  }

  function displayComparePrice() {
    if (state.selectedVariant && state.selectedVariant.compare_price) {
      return state.selectedVariant.compare_price;
    }
    return state.baseComparePrice || "";
  }

  function syncCartButton() {
    if (!cartBtn) return;
    const ok = canAddToCart();
    cartBtn.disabled = !ok;
    cartBtn.classList.toggle("is-disabled", !ok);
    if (state.selectedVariant) {
      cartBtn.dataset.variant = String(state.selectedVariant.id);
    } else {
      delete cartBtn.dataset.variant;
    }
    cartBtn.dataset.quantity = String(state.qty);
    if (cartLabel) {
      cartLabel.textContent = ok
        ? "افزودن به سبد"
        : state.selectedVariant
          ? "ناموجود"
          : "انتخاب تنوع";
    }
  }

  function optionClass(attrId, val, base) {
    const active = Number(state.selected[attrId]) === Number(val.id);
    const compatible = isValueCompatible(attrId, val.id);
    const oos = compatible && !isValueInStock(attrId, val.id);
    return `${base}${active ? " is-active" : ""}${oos ? " is-oos" : ""}${
      compatible ? "" : " is-unavailable"
    }`;
  }

  function renderGroups() {
    if (!groupsEl) return;
    const attrs = visibleAttributes();
    if (!attrs.length) {
      groupsEl.innerHTML =
        state.variants.length > 0
          ? `<p class="ps-page-sub">تنوع‌های این محصول قابل نمایش نیست.</p>`
          : "";
      return;
    }

    groupsEl.innerHTML = attrs
      .map((attr) => {
        const values = getAllValues(attr.id);
        const selected = selectedLabel(attr.id);
        let optionsHtml = "";
        if (isColor(attr)) {
          optionsHtml = `<div class="ps-variant-options">${values
            .map((val) => {
              return `<button type="button" class="${optionClass(
                attr.id,
                val,
                "ps-variant-color"
              )}" data-attr="${attr.id}" data-value="${val.id}" title="${escapeHtml(
                val.value
              )}" aria-label="${escapeHtml(val.value)}">
                <span class="ps-variant-swatch" style="${swatchStyle(val)}" aria-hidden="true"></span>
                <span class="ps-variant-color-name">${escapeHtml(val.value)}</span>
              </button>`;
            })
            .join("")}</div>`;
        } else if (isList(attr)) {
          optionsHtml = `<select class="ps-select ps-variant-select" data-attr="${attr.id}">
            <option value="" disabled ${!state.selected[attr.id] ? "selected" : ""}>انتخاب کنید</option>
            ${values
              .map((val) => {
                const active = Number(state.selected[attr.id]) === Number(val.id);
                const compatible = isValueCompatible(attr.id, val.id);
                const oos = compatible && !isValueInStock(attr.id, val.id);
                const suffix = oos ? " (ناموجود)" : compatible ? "" : "";
                return `<option value="${val.id}" ${active ? "selected" : ""}>${escapeHtml(
                  val.value
                )}${suffix}</option>`;
              })
              .join("")}
          </select>`;
        } else {
          optionsHtml = `<div class="ps-variant-options">${values
            .map((val) => {
              return `<button type="button" class="${optionClass(
                attr.id,
                val,
                "ps-variant-btn"
              )}" data-attr="${attr.id}" data-value="${val.id}">${escapeHtml(
                val.value
              )}</button>`;
            })
            .join("")}</div>`;
        }
        return `<div class="ps-variant-group" data-attr-group="${attr.id}">
          <div class="ps-variant-label">
            <span>${escapeHtml(attr.name)}</span>
            ${selected ? `<span class="ps-variant-selected">${escapeHtml(selected)}</span>` : ""}
          </div>
          ${optionsHtml}
        </div>`;
      })
      .join("");

    groupsEl.querySelectorAll("[data-attr][data-value]").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectValue(Number(btn.dataset.attr), Number(btn.dataset.value));
      });
    });
    groupsEl.querySelectorAll("select[data-attr]").forEach((sel) => {
      sel.addEventListener("change", () => {
        const val = Number(sel.value);
        if (val) selectValue(Number(sel.dataset.attr), val);
      });
    });
  }

  function render() {
    if (priceEl) priceEl.innerHTML = formatPrice(displayPrice());
    if (compareEl) {
      const cmp = displayComparePrice();
      if (cmp) {
        compareEl.hidden = false;
        compareEl.innerHTML = formatPrice(cmp);
      } else {
        compareEl.hidden = true;
        compareEl.textContent = "";
      }
    }
    if (summaryEl) {
      const parts = [];
      visibleAttributes().forEach((attr) => {
        const label = selectedLabel(attr.id);
        if (label) parts.push(`${attr.name}: ${label}`);
      });
      const textEl = summaryEl.querySelector("[data-ps-variant-summary-text]");
      if (parts.length && state.selectedVariant) {
        summaryEl.hidden = false;
        if (textEl) textEl.textContent = parts.join(" · ");
      } else {
        summaryEl.hidden = true;
      }
    }
    if (qtyVal) {
      qtyVal.textContent = window.ShopMoney
        ? window.ShopMoney.formatAmount(state.qty)
        : String(state.qty);
    }
    renderGroups();
    syncCartButton();
    if (window.PulseTheme?.refreshIcons) window.PulseTheme.refreshIcons(host);
    else if (window.lucide) window.lucide.createIcons();
  }

  host.querySelector("[data-ps-qty-dec]")?.addEventListener("click", () => {
    state.qty = Math.max(1, state.qty - 1);
    render();
  });
  host.querySelector("[data-ps-qty-inc]")?.addEventListener("click", () => {
    state.qty += 1;
    render();
  });

  // NextShop parity: start from first in-stock variant so all dimensions are selected
  // and every option chip remains visible for switching.
  if (state.variants.length) {
    const initial =
      state.variants.find((v) => v.in_stock) || state.variants[0] || null;
    if (initial) applyVariant(initial);
  }

  render();
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
