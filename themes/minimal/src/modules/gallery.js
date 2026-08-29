export function initGallery(root = document) {
  root.querySelectorAll("[data-em-gallery]").forEach((gallery) => {
    if (gallery.dataset.bound === "1") return;
    gallery.dataset.bound = "1";
    const main = gallery.querySelector("[data-em-gallery-main]");
    const thumbs = gallery.querySelectorAll("[data-em-gallery-thumb]");
    if (!main || !thumbs.length) return;
    thumbs.forEach((thumb) => {
      thumb.addEventListener("click", () => {
        main.src = thumb.dataset.src || main.src;
        main.alt = thumb.dataset.alt || main.alt;
        thumbs.forEach((t) => t.classList.toggle("is-active", t === thumb));
      });
    });
  });
}
