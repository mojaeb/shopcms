/**
 * Alpine data used by product, catalog, and related templates.
 * These names (vgQty, vgProductVariants, …) are referenced from HTML.
 */
export function registerAlpineData(Alpine, refreshIcons) {
  const refresh = typeof refreshIcons === "function" ? refreshIcons : () => {};

  Alpine.data("vgQty", (start) => ({
    qty: Number(start) || 1,
    adding: false,
    justAdded: false,
    inc() {
      this.qty += 1;
    },
    dec() {
      if (this.qty > 1) this.qty -= 1;
    },
    cartLabel() {
      if (this.adding) return "در حال افزودن...";
      if (this.justAdded) return "اضافه شد";
      return "افزودن به سبد";
    },
  }));

  Alpine.data("vgFilters", () => ({
    open: false,
    toggle() {
      this.open = !this.open;
      this.$nextTick(refresh);
    },
  }));

  Alpine.data("vgTabs", (initial) => ({
    active: initial || "info",
    set(id) {
      this.active = id;
      this.$nextTick(refresh);
    },
  }));

  Alpine.data("vgGallery", () => ({
    images: [],
    index: 0,
    lightboxOpen: false,
    _touchStartX: 0,

    initFromJson(jsonText) {
      try {
        this.images = JSON.parse(jsonText || "[]") || [];
      } catch {
        this.images = [];
      }
      this.$watch("index", () => {
        this.scrollThumbIntoView();
      });
      this.$nextTick(refresh);
    },

    set(i) {
      if (!this.images.length) return;
      const next = ((Number(i) % this.images.length) + this.images.length) % this.images.length;
      if (next === this.index) return;
      this.index = next;
      this.$nextTick(refresh);
    },

    next() {
      if (this.images.length < 2) return;
      this.set(this.index + 1);
    },

    prev() {
      if (this.images.length < 2) return;
      this.set(this.index - 1);
    },

    openLightbox(i) {
      if (typeof i === "number") this.set(i);
      if (!this.images.length) return;
      this.lightboxOpen = true;
      document.body.classList.add("vg-lightbox-open");
      this.$nextTick(refresh);
    },

    closeLightbox() {
      this.lightboxOpen = false;
      document.body.classList.remove("vg-lightbox-open");
    },

    scrollThumbIntoView() {
      const strip = this.$refs.thumbStrip;
      if (!strip) return;
      const active = strip.querySelector(".ns-gallery-thumb.is-active, .vg-gallery-thumb.is-active");
      if (active && active.scrollIntoView) {
        active.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      }
    },

    onTouchStart(e) {
      this._touchStartX = e.changedTouches[0].screenX;
    },

    onTouchEnd(e) {
      if (this.images.length < 2) return;
      const diff = e.changedTouches[0].screenX - this._touchStartX;
      if (Math.abs(diff) < 40) return;
      if (diff > 0) this.prev();
      else this.next();
    },
  }));

  Alpine.data("vgProductVariants", () => ({
    variants: [],
    attributeOptions: [],
    selected: {},
    selectedVariant: null,
    basePrice: "0",
    baseComparePrice: "",
    qty: 1,
    adding: false,
    justAdded: false,

    boot() {
      const root = this.$el;
      this.basePrice = root.dataset.basePrice || "0";
      this.baseComparePrice = root.dataset.baseComparePrice || "";
      const variantsNode = document.getElementById("vg-product-variants");
      const optionsNode = document.getElementById("vg-product-attribute-options");
      try {
        this.variants = variantsNode ? JSON.parse(variantsNode.textContent || "[]") : [];
        this.attributeOptions = optionsNode ? JSON.parse(optionsNode.textContent || "[]") : [];
      } catch {
        this.variants = [];
        this.attributeOptions = [];
      }
      const initial = this.variants.find((v) => v.in_stock) || this.variants[0] || null;
      if (initial) this.applyVariant(initial);
      this.$nextTick(refresh);
    },

    applyVariant(variant) {
      if (!variant) return;
      this.selectedVariant = variant;
      const sel = {};
      (variant.attributes || []).forEach((attr) => {
        sel[attr.attribute_id] = attr.id;
      });
      this.selected = sel;
    },

    isColor(attr) {
      return attr.display_type === "color";
    },

    colorCodes(val) {
      if (val && Array.isArray(val.color_codes) && val.color_codes.length) {
        return val.color_codes;
      }
      const raw = (val && val.color_code) || "";
      return String(raw)
        .split(/[,،/\s]+/)
        .map((p) => p.trim())
        .filter(Boolean)
        .map((p) => (p.charAt(0) === "#" ? p : "#" + p));
    },

    swatchStyle(val) {
      const codes = this.colorCodes(val);
      if (!codes.length) return { "--swatch": "#ccc" };
      if (codes.length === 1) return { "--swatch": codes[0] };
      const n = codes.length;
      const stops = codes
        .map((c, i) => {
          const a = ((i / n) * 100).toFixed(2);
          const b = (((i + 1) / n) * 100).toFixed(2);
          return `${c} ${a}% ${b}%`;
        })
        .join(", ");
      return {
        "--swatch": codes[0],
        "--swatch-multi": `conic-gradient(from 135deg, ${stops})`,
      };
    },

    isList(attr) {
      return attr.display_type === "list" || attr.display_type === "select";
    },

    isButton(attr) {
      return !this.isColor(attr) && !this.isList(attr);
    },

    buttonStyle(attr) {
      return attr.button_style || "text";
    },

    selectedLabel(attrId) {
      const attr = this.attributeOptions.find((a) => Number(a.id) === Number(attrId));
      if (!attr) return "";
      const selectedId = Number(this.selected[attrId]);
      const val = (attr.values || []).find((v) => Number(v.id) === selectedId);
      return val ? val.value : "";
    },

    variantSummary() {
      const parts = [];
      this.visibleAttributes().forEach((attr) => {
        const label = this.selectedLabel(attr.id);
        if (label) parts.push(attr.name + ": " + label);
      });
      return parts.join(" · ");
    },

    isSelected(attrId, valueId) {
      return Number(this.selected[attrId]) === Number(valueId);
    },

    variantMatchesSelection(variant, selection, strictAttrId) {
      const byAttr = {};
      (variant.attributes || []).forEach((a) => {
        byAttr[a.attribute_id] = a.id;
      });

      if (strictAttrId !== undefined && strictAttrId !== null) {
        if (byAttr[strictAttrId] === undefined) return false;
      }

      for (const attrId in selection) {
        if (!Object.prototype.hasOwnProperty.call(selection, attrId)) continue;
        const chosen = Number(selection[attrId]);
        if (byAttr[attrId] === undefined) {
          if (Number(attrId) === Number(strictAttrId)) return false;
          continue;
        }
        if (Number(byAttr[attrId]) !== chosen) return false;
      }
      return true;
    },

    selectValue(attrId, valueId) {
      if (!this.isValueCompatible(attrId, valueId)) return;
      this.selected[attrId] = valueId;

      this.attributeOptions.forEach((attr) => {
        if (Number(attr.id) === Number(attrId)) return;
        const sel = this.selected[attr.id];
        if (!sel) return;
        if (!this.isValueCompatible(attr.id, sel)) {
          delete this.selected[attr.id];
        }
      });

      this.selectedVariant = this.findVariant();
      this.$nextTick(refresh);
    },

    matchingVariants(partialSelected) {
      const selected = partialSelected || this.selected;
      if (!Object.keys(selected).length) return this.variants.slice();
      return this.variants.filter((variant) =>
        this.variantMatchesSelection(variant, selected, null)
      );
    },

    isValueCompatible(attrId, valueId) {
      const trial = Object.assign({}, this.selected);
      trial[attrId] = valueId;
      return this.variants.some((variant) =>
        this.variantMatchesSelection(variant, trial, attrId)
      );
    },

    isValueInStock(attrId, valueId) {
      const trial = Object.assign({}, this.selected);
      trial[attrId] = valueId;
      return this.variants.some((variant) => {
        if (!variant.in_stock) return false;
        return this.variantMatchesSelection(variant, trial, attrId);
      });
    },

    getAvailableValues(attrId) {
      const attr = this.attributeOptions.find((a) => Number(a.id) === Number(attrId));
      if (!attr) return [];
      return (attr.values || []).filter((val) => this.isValueCompatible(attrId, val.id));
    },

    visibleAttributes() {
      return this.attributeOptions.filter((attr) => this.getAvailableValues(attr.id).length > 0);
    },

    needsMoreSelection() {
      return !this.selectedVariant && this.visibleAttributes().length > 0;
    },

    findVariant() {
      const selectedEntries = Object.keys(this.selected)
        .map((k) => ({ attrId: Number(k), valueId: Number(this.selected[k]) }))
        .filter((row) => row.attrId && row.valueId);
      if (!selectedEntries.length) return null;

      const requiredAttrIds = this.visibleAttributes().map((a) => Number(a.id));
      const selectedAttrIds = selectedEntries.map((r) => r.attrId);
      for (let i = 0; i < requiredAttrIds.length; i++) {
        if (selectedAttrIds.indexOf(requiredAttrIds[i]) === -1) return null;
      }

      return (
        this.variants.find((variant) =>
          this.variantMatchesSelection(variant, this.selected, null)
        ) || null
      );
    },

    isValueAvailable(attrId, valueId) {
      return this.isValueCompatible(attrId, valueId);
    },

    formatPrice(amount) {
      const n = Number(amount) || 0;
      return n.toLocaleString("fa-IR") + " تومان";
    },

    displayPrice() {
      return this.selectedVariant ? this.selectedVariant.price : this.basePrice;
    },

    displayComparePrice() {
      if (this.selectedVariant && this.selectedVariant.compare_price) {
        return this.selectedVariant.compare_price;
      }
      return this.baseComparePrice || "";
    },

    canAddToCart() {
      return !!(this.selectedVariant && this.selectedVariant.in_stock);
    },

    cartLabel() {
      if (this.adding) return "در حال افزودن...";
      if (this.justAdded) return "اضافه شد";
      return this.canAddToCart() ? "افزودن به سبد" : "ناموجود";
    },

    incQty() {
      this.qty += 1;
    },

    decQty() {
      if (this.qty > 1) this.qty -= 1;
    },
  }));
}
