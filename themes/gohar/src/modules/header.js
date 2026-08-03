export function initHeader() {
  const header = document.querySelector("[data-gh-header]");
  if (!header || header.dataset.bound === "1") return;
  header.dataset.bound = "1";

  const drawer = header.querySelector("[data-gh-drawer]");
  const openBtn = header.querySelector("[data-gh-open-menu]");
  const closeBtns = header.querySelectorAll("[data-gh-close-menu]");

  const setOpen = (open) => {
    header.classList.toggle("is-drawer-open", open);
    document.documentElement.classList.toggle("gh-scroll-lock", open);
    if (drawer) drawer.setAttribute("aria-hidden", open ? "false" : "true");
    if (openBtn) openBtn.setAttribute("aria-expanded", open ? "true" : "false");
  };

  openBtn?.addEventListener("click", () => setOpen(true));
  closeBtns.forEach((btn) => btn.addEventListener("click", () => setOpen(false)));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });

  const onScroll = () => {
    header.classList.toggle("is-scrolled", window.scrollY > 40);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}
