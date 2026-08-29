import gsap from "gsap";

const INTERVAL = 5.2;
const EASE_IN = "power3.out";
const EASE_OUT = "power2.out";

export function initHero(root = document) {
  const reduce =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const stacked =
    window.matchMedia && window.matchMedia("(max-width: 860px)").matches;

  root.querySelectorAll("[data-em-hero]").forEach((hero) => {
    if (hero.dataset.bound === "1") return;
    hero.dataset.bound = "1";

    const slides = Array.from(hero.querySelectorAll("[data-em-slide]"));
    const dots = Array.from(hero.querySelectorAll("[data-em-dot]"));
    const progress = hero.querySelector("[data-em-progress]");
    if (!slides.length) return;

    let index = Math.max(0, slides.findIndex((el) => el.classList.contains("is-active")));
    let hoverPaused = false;
    let focusPaused = false;
    let offscreen = false;
    let slideTl;
    let progressTween;

    const paused = () => hoverPaused || focusPaused || offscreen;

    const copyOf = (slide) => slide.querySelectorAll(".em-hero-copy > *");
    const mediaOf = (slide) => slide.querySelector(".em-hero-media");

    const clipFrom = () => (stacked ? "inset(100% 0% 0% 0%)" : "inset(0% 100% 0% 0%)");

    const mark = (n) => {
      slides.forEach((el, i) => {
        const on = i === n;
        el.classList.toggle("is-active", on);
        el.setAttribute("aria-hidden", on ? "false" : "true");
      });
      dots.forEach((el, i) => {
        const on = i === n;
        el.classList.toggle("is-active", on);
        el.setAttribute("aria-current", on ? "true" : "false");
      });
    };

    const killClock = () => {
      progressTween?.kill();
      progressTween = null;
    };

    const arm = () => {
      progressTween?.kill();
      progressTween = null;
      if (paused() || reduce || slides.length < 2) return;
      if (progress) {
        gsap.set(progress, { scaleX: 0, transformOrigin: "right center" });
        progressTween = gsap.to(progress, {
          scaleX: 1,
          duration: INTERVAL,
          ease: "none",
          onComplete: () => show(index + 1),
        });
      } else {
        progressTween = gsap.delayedCall(INTERVAL, () => show(index + 1));
      }
    };

    const syncPause = () => {
      hero.classList.toggle("is-paused", paused());
      if (paused()) {
        progressTween?.pause();
      } else {
        progressTween?.resume();
        if (!progressTween && !reduce) arm();
      }
    };

    const enter = (slide, { initial = false } = {}) => {
      const copy = copyOf(slide);
      const media = mediaOf(slide);

      gsap.set(slide, { autoAlpha: 1, zIndex: 2 });

      if (reduce) {
        gsap.set(copy, { autoAlpha: 1, x: 0, y: 0 });
        gsap.set(media, { clipPath: "inset(0% 0% 0% 0%)" });
        return;
      }

      if (initial) {
        gsap.set(copy, { autoAlpha: 1, x: 0, y: 0 });
        gsap.set(media, { clipPath: "inset(0% 0% 0% 0%)" });
        return;
      }

      const dir = document.documentElement.dir === "rtl" ? 1 : -1;
      gsap.set(copy, { autoAlpha: 0, y: 20, x: 18 * dir });
      gsap.set(media, { clipPath: clipFrom() });

      slideTl = gsap.timeline();
      slideTl.to(
        media,
        { clipPath: "inset(0% 0% 0% 0%)", duration: 0.85, ease: EASE_IN },
        0
      );
      slideTl.to(
        copy,
        { autoAlpha: 1, y: 0, x: 0, duration: 0.7, ease: EASE_IN, stagger: 0.09 },
        0.16
      );
    };

    const show = (n, { boot = false } = {}) => {
      const nextIndex = (n + slides.length) % slides.length;
      if (!boot && nextIndex === index) return;

      slideTl?.kill();
      killClock();

      const outgoing = slides[index];
      const incoming = slides[nextIndex];
      index = nextIndex;
      mark(index);

      if (boot) {
        enter(incoming, { initial: true });
        arm();
        return;
      }

      if (reduce) {
        gsap.set(outgoing, { autoAlpha: 0, zIndex: 0 });
        enter(incoming, { initial: true });
        arm();
        return;
      }

      gsap.killTweensOf(outgoing);
      gsap.set(outgoing, { zIndex: 1 });
      gsap.to(outgoing, {
        autoAlpha: 0,
        duration: 0.45,
        ease: EASE_OUT,
        onComplete: () => {
          gsap.set(outgoing, { zIndex: 0 });
          gsap.set(mediaOf(outgoing), { clipPath: "inset(0% 0% 0% 0%)" });
          gsap.set(copyOf(outgoing), { autoAlpha: 0, y: 20, x: 0 });
        },
      });
      enter(incoming);
      arm();
    };

    hero.querySelector("[data-em-next]")?.addEventListener("click", () => show(index + 1));
    hero.querySelector("[data-em-prev]")?.addEventListener("click", () => show(index - 1));
    dots.forEach((dot) => {
      dot.addEventListener("click", () => show(Number(dot.getAttribute("data-em-dot")) || 0));
    });

    hero.addEventListener("mouseenter", () => {
      hoverPaused = true;
      syncPause();
    });
    hero.addEventListener("mouseleave", () => {
      hoverPaused = false;
      syncPause();
    });
    hero.addEventListener("focusin", (event) => {
      if (event.target.closest(".em-hero-copy")) {
        focusPaused = true;
        syncPause();
      }
    });
    hero.addEventListener("focusout", (event) => {
      if (!hero.contains(event.relatedTarget)) {
        focusPaused = false;
        hoverPaused = false;
        syncPause();
      } else if (!event.relatedTarget?.closest(".em-hero-copy")) {
        focusPaused = false;
        syncPause();
      }
    });

    hero.addEventListener("keydown", (event) => {
      if (slides.length < 2) return;
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        show(index + 1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        show(index - 1);
      }
    });

    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver(
        ([entry]) => {
          offscreen = !entry.isIntersecting;
          syncPause();
        },
        { threshold: 0.25 }
      );
      io.observe(hero);
    }

    gsap.set(slides, { autoAlpha: (i) => (i === index ? 1 : 0) });
    show(index, { boot: true });
  });
}
