import {
  createIcons,
  Menu,
  X,
  Search,
  Heart,
  ShoppingCart,
  ShoppingBag,
  User,
  LogIn,
  LogOut,
  LayoutDashboard,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  ArrowRight,
  LayoutGrid,
  Package,
  Truck,
  ShieldCheck,
  BadgeCheck,
  Headphones,
  Minus,
  Plus,
  ImageOff,
  TicketPercent,
  MapPin,
  CreditCard,
  Receipt,
  RotateCcw,
  RefreshCw,
  Lock,
  FileText,
  MessageSquare,
  Download,
  AlertCircle,
  SearchX,
  Pencil,
  Layers,
  Trash2,
} from "lucide";
import gsap from "gsap";
import Swiper from "swiper";
import { Navigation, Pagination, Autoplay } from "swiper/modules";
import htmx from "htmx.org";

import "./styles/main.css";
import { initHeader } from "./modules/header.js";
import { initCarousels, initHeroSlider } from "./modules/carousels.js";
import { initReveals } from "./modules/animations.js";
import { initGallery } from "./modules/gallery.js";
import { initQty } from "./modules/qty.js";
import { initTabs } from "./modules/tabs.js";
import { initVariants } from "./modules/variants.js";

const pulseIcons = {
  Menu,
  X,
  Search,
  Heart,
  ShoppingCart,
  ShoppingBag,
  User,
  LogIn,
  LogOut,
  LayoutDashboard,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  ArrowRight,
  LayoutGrid,
  Package,
  Truck,
  ShieldCheck,
  BadgeCheck,
  Headphones,
  Minus,
  Plus,
  ImageOff,
  TicketPercent,
  MapPin,
  CreditCard,
  Receipt,
  RotateCcw,
  RefreshCw,
  Lock,
  FileText,
  MessageSquare,
  Download,
  AlertCircle,
  SearchX,
  Pencil,
  Layers,
  Trash2,
};

window.htmx = htmx;
window.gsap = gsap;
window.Swiper = Swiper;
window.SwiperModules = { Navigation, Pagination, Autoplay };

function refreshIcons(root = document) {
  const scope = root && root.querySelectorAll ? root : document;
  // Lucide ignores unknown options like `root`; only replace icons in scope.
  const nodes = scope.querySelectorAll
    ? scope.querySelectorAll("[data-lucide]")
    : document.querySelectorAll("[data-lucide]");
  if (!nodes.length && scope !== document) return;
  createIcons({ icons: pulseIcons, attrs: { "stroke-width": 1.75 } });
}

function safeInit(fn, ...args) {
  try {
    fn(...args);
  } catch (err) {
    console.error("[PulseTheme]", err);
  }
}

function boot() {
  // Variants first so a later init failure cannot leave an empty picker.
  safeInit(initVariants);
  safeInit(refreshIcons);
  safeInit(initHeader);
  safeInit(initHeroSlider);
  safeInit(initCarousels);
  safeInit(initReveals, gsap);
  safeInit(initGallery);
  safeInit(initQty);
  safeInit(initTabs);
}

document.addEventListener("DOMContentLoaded", boot);
document.body.addEventListener("htmx:afterSwap", (event) => {
  safeInit(initVariants, event.target);
  safeInit(refreshIcons, event.target);
  safeInit(initCarousels, event.target);
  safeInit(initGallery, event.target);
  safeInit(initQty, event.target);
  safeInit(initTabs, event.target);
});

window.PulseTheme = { refreshIcons, boot };
window.lucide = {
  createIcons(options) {
    if (options && options.root) {
      refreshIcons(options.root);
      return;
    }
    refreshIcons();
  },
};
