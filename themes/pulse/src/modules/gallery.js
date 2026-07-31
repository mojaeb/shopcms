export function initGallery(root = document) {
  root.querySelectorAll("[data-ps-gallery]").forEach((gallery) => {
    if (gallery.dataset.bound === "1") return;
    gallery.dataset.bound = "1";

    const main = gallery.querySelector("[data-ps-gallery-main]");
    const thumbs = [...gallery.querySelectorAll("[data-ps-gallery-thumb]")];
    if (!main || !thumbs.length) return;

    const setActive = (index) => {
      const thumb = thumbs[index];
      if (!thumb) return;
      const src = thumb.dataset.src;
      const alt = thumb.dataset.alt || "";
      if (src) {
        main.src = src;
        main.alt = alt;
      }
      thumbs.forEach((btn, i) => btn.classList.toggle("is-active", i === index));
    };

    thumbs.forEach((btn, index) => {
      btn.addEventListener("click", () => setActive(index));
    });
  });
}
