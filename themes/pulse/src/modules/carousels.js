import Swiper from "swiper";
import { Navigation, Pagination, Autoplay, A11y } from "swiper/modules";

export function initHeroSlider(root = document) {
  root.querySelectorAll("[data-ps-hero]").forEach((el) => {
    if (el.dataset.swiperInit === "1") return;
    el.dataset.swiperInit = "1";

    const shell = el.closest(".ps-hero") || el;
    const slideCount = el.querySelectorAll(".swiper-slide").length;

    new Swiper(el, {
      modules: [Navigation, Pagination, Autoplay, A11y],
      slidesPerView: 1,
      spaceBetween: 0,
      speed: 550,
      autoHeight: false,
      watchOverflow: true,
      // rewind avoids loop clone bugs that resize/jump the hero
      rewind: slideCount > 1,
      loop: false,
      allowTouchMove: true,
      autoplay:
        slideCount > 1
          ? { delay: 5200, disableOnInteraction: false, pauseOnMouseEnter: true }
          : false,
      pagination: {
        el: el.querySelector(".swiper-pagination"),
        clickable: true,
      },
      navigation: {
        nextEl: shell.querySelector(".ps-hero-next"),
        prevEl: shell.querySelector(".ps-hero-prev"),
      },
      a11y: {
        enabled: true,
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
