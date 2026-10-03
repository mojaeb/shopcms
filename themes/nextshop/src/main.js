import {
  createIcons,
  // Navigation / UI
  Menu,
  X,
  Search,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  ArrowRight,
  // Shopping
  ShoppingCart,
  ShoppingBag,
  Heart,
  Package,
  // User / Account
  User,
  LogIn,
  LogOut,
  LayoutDashboard,
  LayoutGrid,
  // Commerce
  Truck,
  ShieldCheck,
  BadgeCheck,
  Headphones,
  CreditCard,
  Receipt,
  TicketPercent,
  RotateCcw,
  Lock,
  // Content
  FileText,
  MessageSquare,
  Phone,
  Smartphone,
  Mail,
  MessageCircle,
  Clock,
  HelpCircle,
  Info,
  // Actions / Misc
  Minus,
  Plus,
  ImageOff,
  Layers,
  MapPin,
  MapPinned,
  Pencil,
  Check,
  CheckCircle2,
  XCircle,
  Map,
  Store,
  SlidersHorizontal,
  Gift,
  Star,
} from "lucide";

import Swiper from "swiper";
import { Navigation, Pagination, Autoplay } from "swiper/modules";
import Alpine from "alpinejs";

import "./styles/main.css";
import { initDiscountTabs } from "./modules/discount.js";
import { registerAlpineData } from "./modules/alpine-data.js";
import { initQty } from "./modules/qty.js";

// ─── Icons ──────────────────────────────────────────────────────────────────

const nsIcons = {
  Menu, X, Search, ChevronDown, ChevronLeft, ChevronRight,
  ArrowLeft, ArrowRight,
  ShoppingCart, ShoppingBag, Heart, Package,
  User, LogIn, LogOut, LayoutDashboard, LayoutGrid,
  Truck, ShieldCheck, BadgeCheck, Headphones, CreditCard,
  Receipt, TicketPercent, RotateCcw, Lock,
  FileText, MessageSquare, Phone, Smartphone,
  Mail, MessageCircle, Clock, HelpCircle, Info,
  Minus, Plus, ImageOff, Layers, MapPin, MapPinned,
  Pencil, Check, CheckCircle2, XCircle, Map, Store,
  SlidersHorizontal,
  Gift,
  Star,
};

function refreshIcons(root = document) {
  createIcons({ icons: nsIcons, attrs: { "stroke-width": 1.75 } });
}

window.lucide = {
  createIcons(options) {
    refreshIcons(options && options.root ? options.root : document);
  },
};

// ─── Swiper ──────────────────────────────────────────────────────────────────

window.Swiper = Swiper;
window.SwiperModules = { Navigation, Pagination, Autoplay };

function initHeroSwipers() {
  document.querySelectorAll("[data-ns-hero]").forEach((el) => {
    if (el.dataset.swiperInit === "1") return;
    const slides = el.querySelectorAll(".swiper-slide");
    if (!slides.length) return;
    el.dataset.swiperInit = "1";
    const multi = slides.length > 1;
    const nextEl = el.querySelector(".ns-slider-next");
    const prevEl = el.querySelector(".ns-slider-prev");
    const paginationEl = el.querySelector(".swiper-pagination");
    // rewind, not loop: loop clones break on dir=rtl and the hero looks frozen
    try {
      new Swiper(el, {
        modules: [Navigation, Pagination, Autoplay],
        loop: false,
        rewind: multi,
        speed: 450,
        watchOverflow: true,
        observer: true,
        observeParents: true,
        autoplay: multi
          ? { delay: 5000, disableOnInteraction: false, pauseOnMouseEnter: true }
          : false,
        pagination: multi && paginationEl ? { el: paginationEl, clickable: true } : undefined,
        navigation: multi && nextEl && prevEl ? { nextEl, prevEl } : undefined,
        a11y: {
          prevSlideMessage: "اسلاید قبلی",
          nextSlideMessage: "اسلاید بعدی",
          paginationBulletMessage: "رفتن به اسلاید {{index}}",
        },
      });
    } catch (err) {
      console.error("[NextShop] hero slider", err);
    }
  });
}

function initCarouselSwipers() {
  document.querySelectorAll("[data-ns-carousel]").forEach((el) => {
    if (el.dataset.swiperInit === "1") return;
    const slides = el.querySelectorAll(".swiper-slide");
    if (!slides.length) return;
    el.dataset.swiperInit = "1";
    const wrap = el.closest(".ns-carousel") || el.parentElement;
    const nextEl = wrap.querySelector(".ns-carousel-next");
    const prevEl = wrap.querySelector(".ns-carousel-prev");
    const opts = {
      modules: [Navigation],
      slidesPerView: "auto",
      spaceBetween: 16,
      speed: 400,
      watchOverflow: true,
      observer: true,
      observeParents: true,
      a11y: { prevSlideMessage: "قبلی", nextSlideMessage: "بعدی" },
    };
    if (nextEl && prevEl) opts.navigation = { nextEl, prevEl };
    try {
      new Swiper(el, opts);
    } catch (err) {
      console.error("[NextShop] carousel", err);
    }
  });
}

// ─── Alpine ──────────────────────────────────────────────────────────────────

Alpine.data("nsHeader", () => ({
  mobileOpen: false,
  searchOpen: false,
  init() {
    this.$watch("mobileOpen", (open) => {
      document.body.classList.toggle("ns-drawer-open", !!open);
      if (open) this.$nextTick(() => refreshIcons());
    });
  },
  openMobile() { this.mobileOpen = true; },
  closeMobile() { this.mobileOpen = false; },
  toggleSearch() {
    this.searchOpen = !this.searchOpen;
    if (this.searchOpen) {
      this.$nextTick(() => {
        const input = this.$refs && this.$refs.searchInput;
        if (input) input.focus();
      });
    }
  },
  closeSearch() { this.searchOpen = false; },
}));

registerAlpineData(Alpine, refreshIcons);
window.Alpine = Alpine;

document.addEventListener("alpine:initialized", () => {
  refreshIcons();
});

function boot() {
  refreshIcons();
  initHeroSwipers();
  initCarouselSwipers();
  initDiscountTabs();
  if (!document.documentElement.__nsAlpineStarted) {
    document.documentElement.__nsAlpineStarted = true;
    Alpine.start();
  }
  initQty();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}

window.NextShopTheme = { refreshIcons };

