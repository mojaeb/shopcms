import "./styles/main.css";
import { initHeader } from "./modules/header.js";
import { initHero } from "./modules/hero.js";
import { initGallery } from "./modules/gallery.js";
import { initQty } from "./modules/qty.js";
import { initVariants } from "./modules/variants.js";
import { initIcons } from "./modules/icons.js";

function boot() {
  initHeader();
  initHero();
  initGallery();
  initQty();
  initVariants();
  initIcons();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}

window.MinimalTheme = { boot };
