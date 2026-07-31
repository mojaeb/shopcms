export function initReveals(gsap) {
  const nodes = gsap.utils.toArray("[data-ps-reveal]");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const markVisible = (el) => {
    el.classList.add("is-visible");
    el.style.opacity = "";
    el.style.visibility = "";
    el.style.transform = "";
  };

  if (reduced) {
    nodes.forEach(markVisible);
    return;
  }

  nodes.forEach((el) => {
    const rect = el.getBoundingClientRect();
    const inView = rect.top < window.innerHeight * 0.94 && rect.bottom > 0;
    if (inView) {
      markVisible(el);
      return;
    }

    gsap.set(el, { autoAlpha: 0, y: 18 });

    const play = () => {
      gsap.to(el, {
        autoAlpha: 1,
        y: 0,
        duration: 0.65,
        ease: "power2.out",
        overwrite: true,
        onComplete: () => markVisible(el),
      });
    };

    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              play();
              io.unobserve(el);
            }
          });
        },
        { rootMargin: "0px 0px -6% 0px", threshold: 0.05 }
      );
      io.observe(el);
    } else {
      markVisible(el);
    }
  });

  const hero = document.querySelector("[data-ps-hero-copy]");
  if (hero) {
    // Opacity only — avoid translateY so the hero box never shifts height.
    gsap.from(hero.children, {
      opacity: 0,
      duration: 0.5,
      stagger: 0.06,
      ease: "power1.out",
      delay: 0.05,
      clearProps: "opacity",
    });
  }
}
