/**
 * ShopCMS modern theme — Alpine + GSAP + Lucide
 */
(function () {
    var ShopModern = (window.ShopModern = window.ShopModern || {});

    ShopModern.refreshIcons = function () {
        if (window.lucide && typeof window.lucide.createIcons === "function") {
            window.lucide.createIcons({
                attrs: { "stroke-width": 1.75 },
                nameAttr: "data-lucide",
            });
        }
    };

    ShopModern.initReveal = function () {
        if (!window.gsap) return;
        var nodes = document.querySelectorAll("[data-vg-reveal]:not([data-vg-revealed])");
        if (!nodes.length) return;

        var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (reduce) {
            nodes.forEach(function (el) {
                el.setAttribute("data-vg-revealed", "1");
                el.style.opacity = "1";
            });
            return;
        }

        if (!("IntersectionObserver" in window)) {
            nodes.forEach(function (el) {
                el.setAttribute("data-vg-revealed", "1");
                gsap.fromTo(
                    el,
                    { y: 24, opacity: 0 },
                    { y: 0, opacity: 1, duration: 0.55, ease: "power2.out", clearProps: "transform,opacity" }
                );
            });
            return;
        }

        var io = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (!entry.isIntersecting) return;
                    var el = entry.target;
                    io.unobserve(el);
                    el.setAttribute("data-vg-revealed", "1");
                    var delay = parseFloat(el.getAttribute("data-vg-delay") || "0") || 0;
                    gsap.fromTo(
                        el,
                        { y: 28, opacity: 0 },
                        {
                            y: 0,
                            opacity: 1,
                            duration: 0.6,
                            delay: delay,
                            ease: "power2.out",
                            clearProps: "transform,opacity",
                        }
                    );
                });
            },
            { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
        );

        nodes.forEach(function (el) {
            gsap.set(el, { opacity: 0 });
            io.observe(el);
        });
    };

    ShopModern.initHeroSlider = function (root) {
        if (!root || !window.gsap) return;
        var track = root.querySelector(".vg-theme-slider-track");
        if (!track) return;
        var slides = track.querySelectorAll(".vg-theme-slide");
        if (slides.length < 2) return;

        root._vgIndex = root._vgIndex || 0;
        function go(i) {
            root._vgIndex = (i + slides.length) % slides.length;
            var slide = slides[root._vgIndex];
            gsap.to(track, {
                scrollLeft: slide.offsetLeft,
                duration: 0.55,
                ease: "power2.inOut",
            });
        }
        root.querySelectorAll("[data-vg-slider-prev]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                go(root._vgIndex - 1);
            });
        });
        root.querySelectorAll("[data-vg-slider-next]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                go(root._vgIndex + 1);
            });
        });
    };

    document.addEventListener("alpine:init", function () {
        Alpine.data("modernHeader", function () {
            return {
                searchOpen: false,
                mobileOpen: false,
                _searchTween: null,

                init: function () {
                    var self = this;
                    ShopModern.refreshIcons();
                    this.$nextTick(function () {
                        self.animateIn();
                        ShopModern.refreshIcons();
                    });
                    this.$watch("mobileOpen", function () {
                        self.$nextTick(ShopModern.refreshIcons);
                    });
                },

                animateIn: function () {
                    if (!window.gsap) return;
                    var el = this.$el;
                    var brand = el.querySelector('[data-vg-anim="brand"]');
                    var nav = el.querySelector('[data-vg-anim="nav"]');
                    var actions = el.querySelector('[data-vg-anim="actions"]');
                    var links = nav ? nav.querySelectorAll("a") : [];
                    var tl = gsap.timeline({
                        defaults: { ease: "power2.out", duration: 0.5, clearProps: "transform,opacity" },
                    });
                    if (brand) tl.fromTo(brand, { y: -12, opacity: 0 }, { y: 0, opacity: 1 }, 0);
                    if (links.length) {
                        tl.fromTo(links, { y: -8, opacity: 0 }, { y: 0, opacity: 1, stagger: 0.04 }, 0.06);
                    }
                    if (actions) tl.fromTo(actions, { y: -8, opacity: 0 }, { y: 0, opacity: 1 }, 0.1);
                },

                toggleSearch: function () {
                    if (this.searchOpen) this.closeSearch();
                    else this.openSearch();
                },

                openSearch: function () {
                    var self = this;
                    this.mobileOpen = false;
                    this.searchOpen = true;
                    this.$nextTick(function () {
                        ShopModern.refreshIcons();
                        var panel = self.$refs.searchPanel;
                        var input = self.$refs.searchInput;
                        if (window.gsap && panel) {
                            if (self._searchTween) self._searchTween.kill();
                            gsap.set(panel, { height: "auto", overflow: "hidden" });
                            var target = panel.offsetHeight;
                            self._searchTween = gsap.fromTo(
                                panel,
                                { height: 0, opacity: 0 },
                                {
                                    height: target,
                                    opacity: 1,
                                    duration: 0.38,
                                    ease: "power2.out",
                                    onComplete: function () {
                                        gsap.set(panel, { height: "auto", overflow: "visible" });
                                        if (input) input.focus();
                                    },
                                }
                            );
                        } else if (input) {
                            input.focus();
                        }
                    });
                },

                closeSearch: function () {
                    var self = this;
                    if (!this.searchOpen) return;
                    var panel = this.$refs.searchPanel;
                    if (window.gsap && panel) {
                        if (this._searchTween) this._searchTween.kill();
                        gsap.set(panel, { overflow: "hidden" });
                        this._searchTween = gsap.to(panel, {
                            height: 0,
                            opacity: 0,
                            duration: 0.28,
                            ease: "power2.in",
                            onComplete: function () {
                                self.searchOpen = false;
                                self.$nextTick(ShopModern.refreshIcons);
                            },
                        });
                    } else {
                        this.searchOpen = false;
                    }
                },
            };
        });

        Alpine.data("vgAccordion", function () {
            return {
                open: null,
                toggle: function (id) {
                    this.open = this.open === id ? null : id;
                    this.$nextTick(ShopModern.refreshIcons);
                },
                isOpen: function (id) {
                    return this.open === id;
                },
            };
        });

        Alpine.data("vgQty", function (start) {
            return {
                qty: Number(start) || 1,
                adding: false,
                justAdded: false,
                inc: function () {
                    this.qty += 1;
                },
                dec: function () {
                    if (this.qty > 1) this.qty -= 1;
                },
                cartLabel: function () {
                    if (this.adding) return "در حال افزودن...";
                    if (this.justAdded) return "اضافه شد";
                    return "افزودن به سبد";
                },
            };
        });

        Alpine.data("vgProductVariants", function () {
            return {
                variants: [],
                attributeOptions: [],
                selected: {},
                selectedVariant: null,
                basePrice: "0",
                baseComparePrice: "",
                qty: 1,
                adding: false,
                justAdded: false,

                boot: function () {
                    var root = this.$el;
                    this.basePrice = root.dataset.basePrice || "0";
                    this.baseComparePrice = root.dataset.baseComparePrice || "";
                    var variantsNode = document.getElementById("vg-product-variants");
                    var optionsNode = document.getElementById("vg-product-attribute-options");
                    try {
                        this.variants = variantsNode ? JSON.parse(variantsNode.textContent || "[]") : [];
                        this.attributeOptions = optionsNode ? JSON.parse(optionsNode.textContent || "[]") : [];
                    } catch (e) {
                        this.variants = [];
                        this.attributeOptions = [];
                    }
                    var initial = this.variants.find(function (v) { return v.in_stock; }) || this.variants[0] || null;
                    if (initial) this.applyVariant(initial);
                    this.$nextTick(ShopModern.refreshIcons);
                },

                applyVariant: function (variant) {
                    if (!variant) return;
                    this.selectedVariant = variant;
                    var sel = {};
                    (variant.attributes || []).forEach(function (attr) {
                        sel[attr.attribute_id] = attr.id;
                    });
                    this.selected = sel;
                },

                isColor: function (attr) {
                    return attr.display_type === "color";
                },

                colorCodes: function (val) {
                    if (val && Array.isArray(val.color_codes) && val.color_codes.length) {
                        return val.color_codes;
                    }
                    var raw = (val && val.color_code) || "";
                    return String(raw)
                        .split(/[,،/\s]+/)
                        .map(function (p) { return p.trim(); })
                        .filter(Boolean)
                        .map(function (p) { return p.charAt(0) === "#" ? p : "#" + p; });
                },

                swatchStyle: function (val) {
                    var codes = this.colorCodes(val);
                    if (!codes.length) {
                        return { "--swatch": "#ccc" };
                    }
                    if (codes.length === 1) {
                        return { "--swatch": codes[0] };
                    }
                    var n = codes.length;
                    var stops = codes.map(function (c, i) {
                        var a = ((i / n) * 100).toFixed(2);
                        var b = (((i + 1) / n) * 100).toFixed(2);
                        return c + " " + a + "% " + b + "%";
                    }).join(", ");
                    return {
                        "--swatch": codes[0],
                        "--swatch-multi": "conic-gradient(from 135deg, " + stops + ")",
                    };
                },

                isList: function (attr) {
                    return attr.display_type === "list" || attr.display_type === "select";
                },

                isButton: function (attr) {
                    // Default unknown display types to button chips
                    return !this.isColor(attr) && !this.isList(attr);
                },

                buttonStyle: function (attr) {
                    return attr.button_style || "text";
                },

                selectedLabel: function (attrId) {
                    var attr = this.attributeOptions.find(function (a) {
                        return Number(a.id) === Number(attrId);
                    });
                    if (!attr) return "";
                    var selectedId = Number(this.selected[attrId]);
                    var val = (attr.values || []).find(function (v) {
                        return Number(v.id) === selectedId;
                    });
                    return val ? val.value : "";
                },

                variantSummary: function () {
                    var self = this;
                    var parts = [];
                    this.visibleAttributes().forEach(function (attr) {
                        var label = self.selectedLabel(attr.id);
                        if (label) parts.push(attr.name + ": " + label);
                    });
                    return parts.join(" · ");
                },

                isSelected: function (attrId, valueId) {
                    return Number(this.selected[attrId]) === Number(valueId);
                },

                variantMatchesSelection: function (variant, selection, strictAttrId) {
                    var byAttr = {};
                    (variant.attributes || []).forEach(function (a) {
                        byAttr[a.attribute_id] = a.id;
                    });

                    if (strictAttrId !== undefined && strictAttrId !== null) {
                        if (byAttr[strictAttrId] === undefined) return false;
                    }

                    for (var attrId in selection) {
                        if (!Object.prototype.hasOwnProperty.call(selection, attrId)) continue;
                        var chosen = Number(selection[attrId]);
                        if (byAttr[attrId] === undefined) {
                            if (Number(attrId) === Number(strictAttrId)) return false;
                            continue;
                        }
                        if (Number(byAttr[attrId]) !== chosen) return false;
                    }
                    return true;
                },

                selectValue: function (attrId, valueId) {
                    if (!this.isValueCompatible(attrId, valueId)) return;
                    this.selected[attrId] = valueId;

                    var self = this;
                    this.attributeOptions.forEach(function (attr) {
                        if (Number(attr.id) === Number(attrId)) return;
                        var sel = self.selected[attr.id];
                        if (!sel) return;
                        if (!self.isValueCompatible(attr.id, sel)) {
                            delete self.selected[attr.id];
                        }
                    });

                    this.selectedVariant = this.findVariant();
                    this.$nextTick(ShopModern.refreshIcons);
                },

                matchingVariants: function (partialSelected) {
                    partialSelected = partialSelected || this.selected;
                    var self = this;
                    if (!Object.keys(partialSelected).length) return this.variants.slice();
                    return this.variants.filter(function (variant) {
                        return self.variantMatchesSelection(variant, partialSelected, null);
                    });
                },

                isValueCompatible: function (attrId, valueId) {
                    var trial = Object.assign({}, this.selected);
                    trial[attrId] = valueId;
                    var self = this;
                    return this.variants.some(function (variant) {
                        return self.variantMatchesSelection(variant, trial, attrId);
                    });
                },

                isValueInStock: function (attrId, valueId) {
                    var trial = Object.assign({}, this.selected);
                    trial[attrId] = valueId;
                    var self = this;
                    return this.variants.some(function (variant) {
                        if (!variant.in_stock) return false;
                        return self.variantMatchesSelection(variant, trial, attrId);
                    });
                },

                getAvailableValues: function (attrId) {
                    var attr = this.attributeOptions.find(function (a) {
                        return Number(a.id) === Number(attrId);
                    });
                    if (!attr) return [];
                    var self = this;
                    return (attr.values || []).filter(function (val) {
                        return self.isValueCompatible(attrId, val.id);
                    });
                },

                visibleAttributes: function () {
                    var self = this;
                    return this.attributeOptions.filter(function (attr) {
                        return self.getAvailableValues(attr.id).length > 0;
                    });
                },

                needsMoreSelection: function () {
                    return !this.selectedVariant && this.visibleAttributes().length > 0;
                },

                findVariant: function () {
                    var selectedEntries = Object.keys(this.selected)
                        .map(function (k) {
                            return { attrId: Number(k), valueId: Number(this.selected[k]) };
                        }, this)
                        .filter(function (row) {
                            return row.attrId && row.valueId;
                        });
                    if (!selectedEntries.length) return null;

                    var requiredAttrIds = this.visibleAttributes().map(function (a) {
                        return Number(a.id);
                    });
                    var selectedAttrIds = selectedEntries.map(function (r) { return r.attrId; });
                    // Wait until every visible attribute has a choice
                    for (var i = 0; i < requiredAttrIds.length; i++) {
                        if (selectedAttrIds.indexOf(requiredAttrIds[i]) === -1) return null;
                    }

                    var self = this;
                    return this.variants.find(function (variant) {
                        return self.variantMatchesSelection(variant, self.selected, null);
                    }) || null;
                },

                isValueAvailable: function (attrId, valueId) {
                    return this.isValueCompatible(attrId, valueId);
                },

                formatPrice: function (amount) {
                    var n = Number(amount) || 0;
                    return n.toLocaleString("fa-IR") + " تومان";
                },

                displayPrice: function () {
                    return this.selectedVariant ? this.selectedVariant.price : this.basePrice;
                },

                displayComparePrice: function () {
                    if (this.selectedVariant && this.selectedVariant.compare_price) {
                        return this.selectedVariant.compare_price;
                    }
                    return this.baseComparePrice || "";
                },

                canAddToCart: function () {
                    return !!(this.selectedVariant && this.selectedVariant.in_stock);
                },

                cartLabel: function () {
                    if (this.adding) return "در حال افزودن...";
                    if (this.justAdded) return "اضافه شد";
                    return this.canAddToCart() ? "افزودن به سبد" : "ناموجود";
                },

                incQty: function () {
                    this.qty += 1;
                },

                decQty: function () {
                    if (this.qty > 1) this.qty -= 1;
                },
            };
        });

        Alpine.data("vgFilters", function () {
            return {
                open: false,
                toggle: function () {
                    this.open = !this.open;
                    this.$nextTick(ShopModern.refreshIcons);
                },
            };
        });

        Alpine.data("vgTabs", function (initial) {
            return {
                active: initial || "info",
                set: function (id) {
                    this.active = id;
                    this.$nextTick(ShopModern.refreshIcons);
                },
            };
        });

        Alpine.data("vgGallery", function () {
            return {
                images: [],
                index: 0,
                lightboxOpen: false,
                _touchStartX: 0,

                initFromJson: function (jsonText) {
                    try {
                        this.images = JSON.parse(jsonText || "[]") || [];
                    } catch (e) {
                        this.images = [];
                    }
                    this.$watch("index", function () {
                        this.scrollThumbIntoView();
                    }.bind(this));
                    this.$nextTick(ShopModern.refreshIcons);
                },

                set: function (i) {
                    if (!this.images.length) return;
                    var next = ((Number(i) % this.images.length) + this.images.length) % this.images.length;
                    if (next === this.index) return;
                    this.index = next;
                    this.$nextTick(ShopModern.refreshIcons);
                },

                next: function () {
                    if (this.images.length < 2) return;
                    this.set(this.index + 1);
                },

                prev: function () {
                    if (this.images.length < 2) return;
                    this.set(this.index - 1);
                },

                openLightbox: function (i) {
                    if (typeof i === "number") this.set(i);
                    if (!this.images.length) return;
                    this.lightboxOpen = true;
                    document.body.classList.add("vg-lightbox-open");
                    this.$nextTick(ShopModern.refreshIcons);
                },

                closeLightbox: function () {
                    this.lightboxOpen = false;
                    document.body.classList.remove("vg-lightbox-open");
                },

                scrollThumbIntoView: function () {
                    var strip = this.$refs.thumbStrip;
                    if (!strip) return;
                    var active = strip.querySelector(".vg-gallery-thumb.is-active");
                    if (active && active.scrollIntoView) {
                        active.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
                    }
                },

                onTouchStart: function (e) {
                    this._touchStartX = e.changedTouches[0].screenX;
                },

                onTouchEnd: function (e) {
                    if (this.images.length < 2) return;
                    var diff = e.changedTouches[0].screenX - this._touchStartX;
                    if (Math.abs(diff) < 40) return;
                    if (diff > 0) this.prev();
                    else this.next();
                },
            };
        });
    });

    function boot() {
        ShopModern.refreshIcons();
        ShopModern.initReveal();
        document.querySelectorAll("[data-vg-hero-slider]").forEach(ShopModern.initHeroSlider);
    }

    document.addEventListener("DOMContentLoaded", boot);
    document.addEventListener("alpine:initialized", function () {
        ShopModern.refreshIcons();
        ShopModern.initReveal();
    });

    // Safe re-init after AJAX catalog updates (no MutationObserver — Lucide DOM swaps would loop)
    ShopModern.afterCatalogUpdate = function () {
        ShopModern.refreshIcons();
        ShopModern.initReveal();
    };
})();
