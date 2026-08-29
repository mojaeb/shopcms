import {
  createIcons,
  Phone,
  Mail,
  MapPin,
  MessageCircle,
  Clock,
  Package,
  HelpCircle,
  ArrowLeft,
  Info,
  BadgeCheck,
  Tag,
  Headphones,
  Smartphone,
  Truck,
} from "lucide";

const icons = {
  Phone,
  Mail,
  MapPin,
  MessageCircle,
  Clock,
  Package,
  HelpCircle,
  ArrowLeft,
  Info,
  BadgeCheck,
  Tag,
  Headphones,
  Smartphone,
  Truck,
};

export function initIcons(root = document) {
  if (!root.querySelector("[data-lucide]")) return;
  createIcons({ icons, attrs: { "stroke-width": 1.5 } });
}
