export function initHeader() {
  const header = document.querySelector("[data-ps-header]");
  if (!header || header.dataset.bound === "1") return;
  header.dataset.bound = "1";

  const drawer = header.querySelector("[data-ps-drawer]");
  const overlay = header.querySelector("[data-ps-overlay]");
  const openBtn = header.querySelector("[data-ps-open-menu]");
  const closeBtns = header.querySelectorAll("[data-ps-close-menu]");

  const setOpen = (open) => {
    header.classList.toggle("is-drawer-open", open);
    document.documentElement.classList.toggle("ps-scroll-lock", open);
    if (drawer) drawer.setAttribute("aria-hidden", open ? "false" : "true");
    if (openBtn) openBtn.setAttribute("aria-expanded", open ? "true" : "false");
  };

  openBtn?.addEventListener("click", () => setOpen(true));
  closeBtns.forEach((btn) => btn.addEventListener("click", () => setOpen(false)));
  overlay?.addEventListener("click", () => setOpen(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });

  let lastY = window.scrollY;
  const onScroll = () => {
    const y = window.scrollY;
    header.classList.toggle("is-scrolled", y > 8);
    header.classList.toggle("is-hidden", y > 120 && y > lastY);
    lastY = y;
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
}
