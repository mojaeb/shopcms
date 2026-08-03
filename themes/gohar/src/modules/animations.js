import { ScrollTrigger } from "gsap/ScrollTrigger";

export function initReveals(gsap) {
  gsap.registerPlugin(ScrollTrigger);

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const heroEls = gsap.utils.toArray("[data-hero]");
  if (heroEls.length && !reduced) {
    gsap
      .timeline({ defaults: { ease: "power3.out" } })
      .from("[data-header-inner]", { yPercent: -100, opacity: 0, duration: 0.8 })
      .from(heroEls, { y: 40, opacity: 0, duration: 1, stagger: 0.12 }, "-=0.4");
  }

  if (!reduced) {
    gsap.utils.toArray("[data-parallax]").forEach((el) => {
      gsap.to(el, {
        yPercent: 18,
        ease: "none",
        scrollTrigger: {
          trigger: el.parentElement || el,
          start: "top top",
          end: "bottom top",
          scrub: true,
        },
      });
    });
  }

  const nodes = gsap.utils.toArray("[data-ps-reveal], .reveal");
  if (reduced) {
    nodes.forEach((el) => {
      el.classList.add("is-visible");
      el.style.opacity = "1";
    });
  } else {
    gsap.set(nodes, { opacity: 0, y: 40 });
    nodes.forEach((el) => {
      gsap.to(el, {
        opacity: 1,
        y: 0,
        duration: 1,
        ease: "power3.out",
        scrollTrigger: { trigger: el, start: "top 85%" },
        onComplete: () => el.classList.add("is-visible"),
      });
    });
  }

  if (!reduced) {
    gsap.utils.toArray("[data-stagger]").forEach((group) => {
      const items = group.querySelectorAll("[data-stagger-item], .ps-card, .gh-cat-tile");
      if (!items.length) return;
      gsap.from(items, {
        opacity: 0,
        y: 50,
        duration: 0.9,
        ease: "power3.out",
        stagger: 0.12,
        scrollTrigger: { trigger: group, start: "top 80%" },
      });
    });

    gsap.utils.toArray("[data-title]").forEach((el) => {
      gsap.from(el, {
        opacity: 0,
        y: 60,
        duration: 1.1,
        ease: "power4.out",
        scrollTrigger: { trigger: el, start: "top 88%" },
      });
    });

    gsap.utils.toArray("[data-count]").forEach((el) => {
      const target = Number(el.dataset.count);
      const obj = { val: 0 };
      ScrollTrigger.create({
        trigger: el,
        start: "top 85%",
        once: true,
        onEnter: () =>
          gsap.to(obj, {
            val: target,
            duration: 2,
            ease: "power2.out",
            onUpdate: () => {
              el.textContent = Math.floor(obj.val).toLocaleString("fa-IR");
            },
          }),
      });
    });

  }

  initMarquee(reduced);
}

/**
 * Seamless infinite marquee.
 * Ensures one .marquee-group ≥ viewport, clones it once (track = 2 equal copies),
 * then CSS animates translateX(-50%) so the loop has no jump.
 * Direction: physical leftward (items travel right→left). See main.css comment.
 */
export function initMarquee(reducedMotion) {
  const reduced =
    typeof reducedMotion === "boolean"
      ? reducedMotion
      : window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const setup = () => {
    document.querySelectorAll("[data-marquee]").forEach((track) => {
      if (track.dataset.marqueeInit === "1") return;

      // Strip any prior clones (HTMX re-entry / double boot safety).
      track.querySelectorAll(".marquee-group[aria-hidden='true']").forEach((n) => n.remove());

      let group = track.querySelector(".marquee-group");
      if (!group) {
        group = document.createElement("div");
        group.className = "marquee-group";
        while (track.firstChild) group.appendChild(track.firstChild);
        track.appendChild(group);
      }

      // Grow source until it spans ≥ viewport (no empty gaps in the loop).
      const viewport = Math.max(
        track.parentElement?.clientWidth || 0,
        window.innerWidth || 0,
        1
      );
      const seed = Array.from(group.children);
      let guard = 0;
      while (seed.length && group.scrollWidth < viewport && guard < 12) {
        seed.forEach((n) => group.appendChild(n.cloneNode(true)));
        guard += 1;
      }

      // If layout still reports 0 (fonts/images), retry once after paint.
      if (!group.scrollWidth && seed.length && track.dataset.marqueeRetry !== "1") {
        track.dataset.marqueeRetry = "1";
        requestAnimationFrame(setup);
        return;
      }

      const clone = group.cloneNode(true);
      clone.setAttribute("aria-hidden", "true");
      track.appendChild(clone);

      // Duration scales gently with content width (~40px/s, clamped).
      const shift = group.scrollWidth || viewport;
      const seconds = Math.min(48, Math.max(18, shift / 40));
      track.style.setProperty("--marquee-duration", `${seconds}s`);

      track.dataset.marqueeInit = "1";
      if (!reduced) track.classList.add("is-animating");
    });
  };

  // Wait for webfonts so scrollWidth matches painted text width.
  if (document.fonts?.ready) {
    document.fonts.ready.then(setup).catch(setup);
  } else {
    setup();
  }
}
