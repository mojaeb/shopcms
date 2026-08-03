import Swiper from "swiper";
import { Navigation, Pagination, Autoplay, A11y, EffectFade } from "swiper/modules";

export function initHeroSlider(root = document) {
  root.querySelectorAll("[data-ps-hero], [data-gh-hero]").forEach((el) => {
    if (el.dataset.swiperInit === "1") return;
    el.dataset.swiperInit = "1";

    const shell = el.closest(".gh-hero, .ps-hero") || el;
    const slideCount = el.querySelectorAll(".swiper-slide").length;
    const delay = Number(el.dataset.interval) || 5200;
    const autoplayOff = el.dataset.autoplay === "0";
    const useFade = el.hasAttribute("data-gh-hero");

    new Swiper(el, {
      modules: [Navigation, Pagination, Autoplay, A11y, EffectFade],
      slidesPerView: 1,
      spaceBetween: 0,
      speed: useFade ? 900 : 550,
      effect: useFade ? "fade" : "slide",
      fadeEffect: useFade ? { crossFade: true } : undefined,
      autoHeight: false,
      watchOverflow: true,
      // rewind avoids loop clone bugs that resize/jump the hero
      rewind: slideCount > 1,
      loop: false,
      allowTouchMove: true,
      autoplay:
        slideCount > 1 && !autoplayOff
          ? { delay, disableOnInteraction: false, pauseOnMouseEnter: true }
          : false,
      pagination: {
        el: el.querySelector(".swiper-pagination"),
        clickable: true,
      },
      navigation: {
        nextEl: shell.querySelector(".gh-hero-next, .ps-hero-next"),
        prevEl: shell.querySelector(".gh-hero-prev, .ps-hero-prev"),
      },
      a11y: {
        enabled: true,
        prevSlideMessage: "اسلاید قبلی",
        nextSlideMessage: "اسلاید بعدی",
      },
      on: {
        init(swiper) {
          swiper.el.style.height = "100%";
          if (swiper.wrapperEl) swiper.wrapperEl.style.height = "100%";
        },
      },
    });
  });
}

export function initCarousels(root = document) {
  root.querySelectorAll("[data-ps-carousel]").forEach((el) => {
    if (el.dataset.swiperInit === "1") return;
    el.dataset.swiperInit = "1";
    const wrap = el.closest(".ps-carousel");
    new Swiper(el, {
      modules: [Navigation],
      slidesPerView: 1.25,
      spaceBetween: 12,
      autoHeight: false,
      watchOverflow: true,
      breakpoints: {
        640: { slidesPerView: 2.2, spaceBetween: 14 },
        900: { slidesPerView: 3.1, spaceBetween: 16 },
        1100: { slidesPerView: 4, spaceBetween: 18 },
      },
      navigation: {
        nextEl: wrap?.querySelector(".ps-carousel-next"),
        prevEl: wrap?.querySelector(".ps-carousel-prev"),
      },
    });
  });
}
