import Swiper from "swiper";
import { Navigation, Keyboard, A11y, Thumbs, Zoom } from "swiper/modules";

function faNum(value) {
  if (window.ShopMoney?.formatAmount) return window.ShopMoney.formatAmount(value);
  return String(value ?? "").replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[d]);
}

function focusables(root) {
  return [...root.querySelectorAll(
    'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )].filter((el) => !el.hasAttribute("disabled") && el.getAttribute("aria-hidden") !== "true");
}

export function initGallery(root = document) {
  root.querySelectorAll("[data-ps-gallery]").forEach((gallery) => {
    if (gallery.dataset.bound === "1") return;
    gallery.dataset.bound = "1";
    bindGallery(gallery);
  });
}

function bindGallery(gallery) {
  const mainEl = gallery.querySelector("[data-ps-gallery-main]");
  const thumbsEl = gallery.querySelector("[data-ps-gallery-thumbs]");
  const lightbox = gallery.querySelector("[data-ps-lightbox]");
  if (!mainEl) return;

  const slideCount = mainEl.querySelectorAll(".swiper-slide").length;
  let lastFocus = null;
  let open = false;

  const thumbsSwiper = thumbsEl
    ? new Swiper(thumbsEl, {
        modules: [A11y],
        slidesPerView: "auto",
        spaceBetween: 8,
        watchSlidesProgress: true,
        watchOverflow: true,
        centerInsufficientSlides: true,
        a11y: { enabled: true },
      })
    : null;

  const mainSwiper = new Swiper(mainEl, {
    modules: [Navigation, Keyboard, A11y, Thumbs],
    slidesPerView: 1,
    spaceBetween: 0,
    speed: 420,
    rewind: slideCount > 1,
    watchOverflow: true,
    thumbs: thumbsSwiper ? { swiper: thumbsSwiper } : undefined,
    navigation: {
      nextEl: gallery.querySelector("[data-ps-gallery-next]"),
      prevEl: gallery.querySelector("[data-ps-gallery-prev]"),
    },
    keyboard: { enabled: true, onlyInViewport: true },
    a11y: { enabled: true },
    on: {
      click(swiper, event) {
        if (!swiper.allowClick || !lightbox) return;
        if (event.target.closest("button")) return;
        openLightbox(swiper.clickedIndex ?? swiper.activeIndex ?? 0);
      },
    },
  });

  if (!lightbox) return;

  if (lightbox.parentElement !== document.body) {
    document.body.appendChild(lightbox);
  }

  const dialog = lightbox.querySelector(".ps-lightbox-dialog");
  const counter = lightbox.querySelector("[data-ps-lightbox-counter]");
  const closeBtn = lightbox.querySelector(".ps-lightbox-close");

  const lightboxSwiper = new Swiper(lightbox.querySelector("[data-ps-lightbox-swiper]"), {
    modules: [Navigation, Keyboard, A11y, Zoom],
    slidesPerView: 1,
    spaceBetween: 12,
    speed: 380,
    rewind: slideCount > 1,
    zoom: { maxRatio: 3, minRatio: 1, toggle: true },
    keyboard: { enabled: false },
    navigation: {
      nextEl: lightbox.querySelector("[data-ps-lightbox-next]"),
      prevEl: lightbox.querySelector("[data-ps-lightbox-prev]"),
    },
    a11y: { enabled: true },
    on: {
      slideChange(swiper) {
        syncCounter(swiper.activeIndex);
        mainSwiper.slideTo(swiper.activeIndex);
      },
    },
  });

  function syncCounter(index) {
    if (!counter) return;
    counter.textContent = slideCount > 1
      ? `${faNum(index + 1)} / ${faNum(slideCount)}`
      : "";
  }

  function openLightbox(index) {
    const i = Math.max(0, Number(index) || 0);
    lastFocus = document.activeElement;
    open = true;
    lightbox.classList.add("is-open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.classList.add("ps-lightbox-open");
    lightboxSwiper.slideTo(i, 0);
    lightboxSwiper.zoom.out();
    lightboxSwiper.keyboard?.enable?.();
    mainSwiper.keyboard?.disable?.();
    syncCounter(i);
    (closeBtn || dialog)?.focus();
  }

  function closeLightbox() {
    if (!open) return;
    open = false;
    lightboxSwiper.zoom.out();
    lightboxSwiper.keyboard?.disable?.();
    mainSwiper.keyboard?.enable?.();
    lightbox.classList.remove("is-open");
    lightbox.setAttribute("aria-hidden", "true");
    document.body.classList.remove("ps-lightbox-open");
    if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
  }

  lightbox.querySelectorAll("[data-ps-lightbox-close]").forEach((el) => {
    el.addEventListener("click", closeLightbox);
  });
  lightbox.querySelector("[data-ps-zoom-in]")?.addEventListener("click", (e) => {
    e.stopPropagation();
    lightboxSwiper.zoom.in();
  });
  lightbox.querySelector("[data-ps-zoom-out]")?.addEventListener("click", (e) => {
    e.stopPropagation();
    lightboxSwiper.zoom.out();
  });

  gallery.querySelectorAll("[data-ps-gallery-open]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const slide = btn.closest(".swiper-slide");
      const index = slide && slide.parentElement
        ? [...slide.parentElement.children].indexOf(slide)
        : mainSwiper.activeIndex;
      openLightbox(index);
    });
  });

  lightbox.addEventListener("keydown", (e) => {
    if (!open) return;
    if (e.key === "Escape") {
      e.preventDefault();
      closeLightbox();
      return;
    }
    if (e.key !== "Tab" || !dialog) return;
    const items = focusables(dialog);
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  });
}
