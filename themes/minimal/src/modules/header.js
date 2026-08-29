export function initHeader() {
  const header = document.getElementById("em-header");
  if (!header || header.dataset.bound === "1") return;
  header.dataset.bound = "1";

  const navBtn = document.getElementById("em-nav-toggle");
  const searchBtn = document.getElementById("em-search-toggle");

  navBtn?.addEventListener("click", () => {
    const open = header.classList.toggle("is-nav");
    navBtn.setAttribute("aria-expanded", open ? "true" : "false");
  });

  searchBtn?.addEventListener("click", () => {
    header.classList.toggle("is-search");
    const input = header.querySelector(".em-search input");
    if (header.classList.contains("is-search") && input) input.focus();
  });
}
