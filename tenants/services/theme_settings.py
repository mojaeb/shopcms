"""Per-store theme settings (JSON) helpers."""

from __future__ import annotations

import copy
from typing import Any

from tenants.models import Store, StoreSetting
from tenants.services.cache import StoreCacheService

THEME_GROUP = "theme"
THEME_CONFIG_KEY = "config"

DEFAULT_HERO_SLIDE: dict[str, Any] = {
    "image": "",
    "thumbnail": "",
    "title": "",
    "text": "",
    "button_text": "خرید کنید",
    "button_link": "/products/",
    "background_color": "#f6f4f1",
}

DEFAULT_TRUST_BADGE: dict[str, Any] = {
    "image": "",
    "link": "",
}

DEFAULT_THEME_CONFIG: dict[str, Any] = {
    "logo": "",
    "colors": {
        "primary": "#0f766e",
        "background": "#f8fafc",
        "text": "#0f172a",
    },
    "hero": {
        "slides": [],
    },
    "trust_badges": {
        "enamad": copy.deepcopy(DEFAULT_TRUST_BADGE),
        "badge2": copy.deepcopy(DEFAULT_TRUST_BADGE),
    },
}

SAMPLE_HERO_SLIDE: dict[str, Any] = {
    "image": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=1200&q=80",
    "thumbnail": "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?auto=format&fit=crop&w=80&q=40",
    "title": "کشف کنید، انتخاب کنید، بدرخشید",
    "text": "مجموعه‌های منتخب برای هر سلیقه — با انتخابی دقیق و پرداخت امن.",
    "button_text": "خرید کنید",
    "button_link": "/products/",
    "background_color": "#f6f4f1",
}


def _deep_merge(base: dict, overlay: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in (overlay or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _normalize_slide(raw: Any) -> dict[str, Any]:
    slide = copy.deepcopy(DEFAULT_HERO_SLIDE)
    if not isinstance(raw, dict):
        return slide
    for key in DEFAULT_HERO_SLIDE:
        if key in raw and raw[key] is not None:
            slide[key] = raw[key]
    return slide


def _normalize_trust_badge(raw: Any) -> dict[str, Any]:
    badge = copy.deepcopy(DEFAULT_TRUST_BADGE)
    if not isinstance(raw, dict):
        return badge
    for key in DEFAULT_TRUST_BADGE:
        if key in raw and raw[key] is not None:
            badge[key] = str(raw[key]).strip()
    return badge


def normalize_theme_config(raw: Any) -> dict[str, Any]:
    """Merge stored JSON onto defaults and normalize hero slides."""
    if not isinstance(raw, dict):
        raw = {}
    merged = _deep_merge(DEFAULT_THEME_CONFIG, raw)
    slides_raw = (merged.get("hero") or {}).get("slides") or []
    if not isinstance(slides_raw, list):
        slides_raw = []
    merged["hero"] = {"slides": [_normalize_slide(s) for s in slides_raw]}
    colors = merged.get("colors") or {}
    if not isinstance(colors, dict):
        colors = {}
    merged["colors"] = _deep_merge(DEFAULT_THEME_CONFIG["colors"], colors)
    if merged.get("logo") is None:
        merged["logo"] = ""
    trust_raw = merged.get("trust_badges") or {}
    if not isinstance(trust_raw, dict):
        trust_raw = {}
    merged["trust_badges"] = {
        "enamad": _normalize_trust_badge(trust_raw.get("enamad")),
        "badge2": _normalize_trust_badge(trust_raw.get("badge2")),
    }
    return merged


class ThemeSettingsService:
    """Read/write store theme.config JSON."""

    def __init__(self):
        self.cache_service = StoreCacheService()

    def get_theme_settings(self, store: Store | None) -> dict[str, Any]:
        if not store:
            return copy.deepcopy(DEFAULT_THEME_CONFIG)
        try:
            setting = StoreSetting.objects.get(
                store=store, group=THEME_GROUP, key=THEME_CONFIG_KEY
            )
            return normalize_theme_config(setting.value)
        except StoreSetting.DoesNotExist:
            return copy.deepcopy(DEFAULT_THEME_CONFIG)

    def get_hero_slides(self, store: Store | None) -> list[dict[str, Any]]:
        config = self.get_theme_settings(store)
        slides = (config.get("hero") or {}).get("slides") or []
        return [s for s in slides if isinstance(s, dict) and (s.get("image") or s.get("title") or s.get("text"))]

    def update_theme_settings(self, store: Store, data: dict) -> dict[str, Any]:
        normalized = normalize_theme_config(data)
        StoreSetting.objects.update_or_create(
            store=store,
            group=THEME_GROUP,
            key=THEME_CONFIG_KEY,
            defaults={
                "value": normalized,
                "value_type": "json",
                "description": "تنظیمات تم فروشگاه",
            },
        )
        self.cache_service.invalidate_store(store)
        return normalized

    def ensure_sample_config(self, store: Store) -> dict[str, Any]:
        """Create a sample theme.config if missing (for seeds)."""
        existing = StoreSetting.objects.filter(
            store=store, group=THEME_GROUP, key=THEME_CONFIG_KEY
        ).first()
        if existing:
            return normalize_theme_config(existing.value)
        sample = copy.deepcopy(DEFAULT_THEME_CONFIG)
        sample["hero"]["slides"] = [copy.deepcopy(SAMPLE_HERO_SLIDE)]
        return self.update_theme_settings(store, sample)
