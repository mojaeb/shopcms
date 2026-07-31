(function () {
  function refreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons({
        attrs: { "stroke-width": 1.75 },
        nameAttr: "data-lucide",
      });
    }
  }

  function initHeroSwipers() {
    if (typeof Swiper === "undefined") return;
    document.querySelectorAll("[data-ns-hero]").forEach(function (el) {
      var slides = el.querySelectorAll(".swiper-slide");
      if (!slides.length) return;
      var multi = slides.length > 1;
      var nextEl = el.querySelector(".ns-slider-next");
      var prevEl = el.querySelector(".ns-slider-prev");
      var paginationEl = el.querySelector(".swiper-pagination");
      new Swiper(el, {
        loop: multi,
        speed: 450,
        autoplay: multi
          ? { delay: 5000, disableOnInteraction: false, pauseOnMouseEnter: true }
          : false,
        pagination: multi && paginationEl
          ? { el: paginationEl, clickable: true }
          : undefined,
        navigation: multi && nextEl && prevEl
          ? { nextEl: nextEl, prevEl: prevEl }
          : undefined,
        a11y: {
          prevSlideMessage: "اسلاید قبلی",
          nextSlideMessage: "اسلاید بعدی",
          paginationBulletMessage: "رفتن به اسلاید {{index}}",
        },
      });
    });
  }

  function initCarouselSwipers() {
    if (typeof Swiper === "undefined") return;
    document.querySelectorAll("[data-ns-carousel]").forEach(function (el) {
      var slides = el.querySelectorAll(".swiper-slide");
      if (!slides.length) return;
      var wrap = el.closest(".ns-carousel") || el.parentElement;
      var nextEl = wrap.querySelector(".ns-carousel-next");
      var prevEl = wrap.querySelector(".ns-carousel-prev");
      var opts = {
        slidesPerView: "auto",
        spaceBetween: 16,
        speed: 400,
        watchOverflow: true,
        a11y: {
          prevSlideMessage: "قبلی",
          nextSlideMessage: "بعدی",
        },
      };
      if (nextEl && prevEl) {
        opts.navigation = { nextEl: nextEl, prevEl: prevEl };
      }
      new Swiper(el, opts);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    refreshIcons();
    initHeroSwipers();
    initCarouselSwipers();
  });

  document.addEventListener("alpine:init", function () {
    if (!window.Alpine) return;
    Alpine.data("nsHeader", function () {
      return {
        mobileOpen: false,
        searchOpen: false,
        init: function () {
          var self = this;
          this.$watch("mobileOpen", function (open) {
            document.body.classList.toggle("ns-drawer-open", !!open);
            if (open) {
              self.$nextTick(function () {
                if (window.lucide && typeof window.lucide.createIcons === "function") {
                  window.lucide.createIcons({
                    attrs: { "stroke-width": 1.75 },
                    nameAttr: "data-lucide",
                  });
                }
              });
            }
          });
        },
        openMobile: function () { this.mobileOpen = true; },
        closeMobile: function () { this.mobileOpen = false; },
        toggleSearch: function () {
          this.searchOpen = !this.searchOpen;
          var self = this;
          if (this.searchOpen) {
            this.$nextTick(function () {
              var input = self.$refs && self.$refs.searchInput;
              if (input) input.focus();
            });
          }
        },
        closeSearch: function () { this.searchOpen = false; },
      };
    });
  });
})();
