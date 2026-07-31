"""Shortcode parser and renderer.

Supports:
  [image src="URL" alt="..." /]
  [grid-1-2]...[/grid-1-2]
  Custom store shortcodes with HTML templates using {{attr}} and {{content}}.
"""

from __future__ import annotations

import re
from html import escape
from typing import Any

from django.core.cache import cache

CACHE_TTL = 60 * 10
MAX_PASSES = 20

# Self-closing: [name attrs /] or [name attrs/]
_SELF_RE = re.compile(
    r"\[(?P<name>[a-zA-Z][\w-]*)(?P<attrs>[^\]]*?)\/\]",
    re.DOTALL,
)
# Innermost paired shortcodes (body has no nested [tag ...)
_PAIR_RE = re.compile(
    r"\[(?P<name>[a-zA-Z][\w-]*)(?P<attrs>[^\]]*?)\]"
    r"(?P<body>(?:(?!\[[a-zA-Z][\w-]*).)*?)"
    r"\[/(?P=name)\]",
    re.DOTALL,
)
_ATTR_RE = re.compile(
    r"""([a-zA-Z_][\w-]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'\]]+))""",
)

# Built-in shortcodes (always available; store DB entries with same name override).
BUILTIN_SHORTCODES: dict[str, dict[str, Any]] = {
    "image": {
        "label": "تصویر",
        "description": 'درج تصویر. مثال: [image src="https://..." alt="توضیح"/]',
        "is_self_closing": True,
        "html_template": (
            '<img src="{{src}}" alt="{{alt}}" class="sc-image" loading="lazy" />'
        ),
        "example": '[image src="https://example.com/photo.jpg" alt="نمونه"/]',
    },
    "grid-1-2": {
        "label": "گرید ۱×۲",
        "description": "دو ستون در دسکتاپ، یک ستون در موبایل",
        "is_self_closing": False,
        "html_template": '<div class="sc-grid sc-grid-1-2">{{content}}</div>',
        "example": "[grid-1-2]\n[feature title=\"عنوان ۱\" text=\"توضیح ۱\"/]\n[feature title=\"عنوان ۲\" text=\"توضیح ۲\"/]\n[/grid-1-2]",
    },
    "grid-1-3": {
        "label": "گرید ۱×۳",
        "description": "سه ستون در دسکتاپ، یک ستون در موبایل",
        "is_self_closing": False,
        "html_template": '<div class="sc-grid sc-grid-1-3">{{content}}</div>',
        "example": "[grid-1-3]\n[feature title=\"۱\" text=\"...\"/]\n[feature title=\"۲\" text=\"...\"/]\n[feature title=\"۳\" text=\"...\"/]\n[/grid-1-3]",
    },
    "html": {
        "label": "HTML خام",
        "description": "خروجی بدون تغییر محتوا (برای HTML سفارشی)",
        "is_self_closing": False,
        "html_template": "{{content}}",
        "example": "[html]<div class=\"custom\">...</div>[/html]",
    },
    "lead": {
        "label": "متن مقدماتی",
        "description": "پاراگراف بزرگ معرفی در ابتدای صفحه",
        "is_self_closing": True,
        "html_template": '<p class="sc-lead">{{text}}</p>',
        "example": '[lead text="معرفی کوتاه فروشگاه شما"/]',
    },
    "heading": {
        "label": "عنوان بخش",
        "description": "عنوان بخش با توضیح کوتاه اختیاری",
        "is_self_closing": True,
        "html_template": (
            '<header class="sc-heading">'
            '<h2 class="sc-heading-title">{{title}}</h2>'
            '<p class="sc-heading-text">{{text}}</p>'
            "</header>"
        ),
        "example": '[heading title="چرا ما" text="سه دلیل برای خرید مطمئن"/]',
    },
    "section": {
        "label": "بخش صفحه",
        "description": "جعبه بخش برای گروه‌بندی محتوا. tone=soft|plain|cta",
        "is_self_closing": False,
        "html_template": '<section class="sc-section" data-tone="{{tone}}">{{content}}</section>',
        "example": '[section tone="soft"]\n[heading title="عنوان" text="توضیح"/]\n[/section]',
    },
    "split": {
        "label": "اسپلیت تصویر/متن",
        "description": "دو ستون: تصویر + محتوا",
        "is_self_closing": False,
        "html_template": (
            '<div class="sc-split">'
            '<div class="sc-split-media">'
            '<img src="{{image}}" alt="{{alt}}" loading="lazy" />'
            "</div>"
            '<div class="sc-split-body">{{content}}</div>'
            "</div>"
        ),
        "example": (
            '[split image="https://example.com/a.jpg" alt="فروشگاه"]\n'
            '[heading title="داستان ما" text=""/]\n'
            '[lead text="توضیح کوتاه"/]\n'
            "[/split]"
        ),
    },
    "prose": {
        "label": "متن بدنه",
        "description": "پاراگراف متنی خوانا",
        "is_self_closing": True,
        "html_template": '<p class="sc-prose">{{text}}</p>',
        "example": '[prose text="متن کامل بخش درباره ما"/]',
    },
    "feature": {
        "label": "کارت ویژگی",
        "description": "کارت عنوان + توضیح برای بخش درباره ما",
        "is_self_closing": True,
        "html_template": (
            '<div class="sc-feature">'
            '<span class="sc-feature-icon" aria-hidden="true"><i data-lucide="{{icon}}"></i></span>'
            '<div class="sc-feature-copy">'
            '<strong class="sc-feature-title">{{title}}</strong>'
            '<p class="sc-feature-text">{{text}}</p>'
            "</div>"
            "</div>"
        ),
        "example": '[feature icon="truck" title="ارسال سریع" text="تحویل ۲ تا ۴ روزه سراسر کشور"/]',
    },
    "contact-item": {
        "label": "آیتم تماس",
        "description": "کارت تماس با برچسب، مقدار و لینک",
        "is_self_closing": True,
        "html_template": (
            '<a class="sc-contact-item" href="{{href}}">'
            '<span class="sc-contact-icon" aria-hidden="true"><i data-lucide="{{icon}}"></i></span>'
            '<span class="sc-contact-copy">'
            '<span class="sc-contact-label">{{label}}</span>'
            '<span class="sc-contact-value">{{value}}</span>'
            "</span>"
            '<span class="sc-contact-go" aria-hidden="true"><i data-lucide="arrow-left"></i></span>'
            "</a>"
        ),
        "example": '[contact-item icon="phone" label="تلفن" value="۰۲۱-۱۲۳۴۵۶۷۸" href="tel:+982112345678"/]',
    },
    "cta": {
        "label": "دکمه فراخوان",
        "description": "دکمه CTA لینک‌دار",
        "is_self_closing": True,
        "html_template": (
            '<p class="sc-cta-wrap">'
            '<a class="sc-cta" href="{{href}}">{{label}} <i data-lucide="arrow-left"></i></a>'
            "</p>"
        ),
        "example": '[cta label="مشاهده محصولات" href="/products/"/]',
    },
    "note": {
        "label": "نکته / باکس اطلاع",
        "description": "باکس برجسته برای نکته یا راهنما",
        "is_self_closing": True,
        "html_template": (
            '<aside class="sc-note">'
            '<span class="sc-note-icon" aria-hidden="true"><i data-lucide="info"></i></span>'
            '<p class="sc-note-text">{{text}}</p>'
            "</aside>"
        ),
        "example": '[note text="پاسخ‌گویی شنبه تا پنج‌شنبه ۹ تا ۱۸"/]',
    },
}


def parse_attrs(attr_string: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in _ATTR_RE.finditer(attr_string or ""):
        key = match.group(1)
        value = match.group(2) if match.group(2) is not None else (
            match.group(3) if match.group(3) is not None else match.group(4) or ""
        )
        attrs[key] = value
    return attrs


def _render_template(template: str, context: dict[str, str], *, escape_attrs: bool = True) -> str:
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key == "content":
            return context.get("content", "")
        value = context.get(key, "")
        return escape(value, quote=True) if escape_attrs else value

    return re.sub(r"\{\{\s*([a-zA-Z_][\w-]*)\s*\}\}", replacer, template)


def _cache_key(store_id: int) -> str:
    return f"cms:{store_id}:shortcodes"


def invalidate_shortcode_cache(store) -> None:
    if store is None:
        return
    cache.delete(_cache_key(store.id))


def get_shortcode_definitions(store) -> dict[str, dict[str, Any]]:
    """Merge builtins with store-defined shortcodes (store overrides)."""
    defs = {name: {**meta, "name": name, "is_system": True} for name, meta in BUILTIN_SHORTCODES.items()}
    if store is None:
        return defs

    cached = cache.get(_cache_key(store.id))
    if cached is not None:
        return cached

    from cms.models import Shortcode

    for sc in Shortcode.objects.filter(store=store, is_active=True):
        defs[sc.name] = {
            "name": sc.name,
            "label": sc.label,
            "description": sc.description,
            "is_self_closing": sc.is_self_closing,
            "html_template": sc.html_template,
            "example": sc.example,
            "is_system": False,
            "id": sc.id,
        }

    cache.set(_cache_key(store.id), defs, CACHE_TTL)
    return defs


def expand_shortcodes(text: str, store=None) -> str:
    """Expand shortcodes in rich text. Safe to call with empty/None text."""
    if not text:
        return text or ""

    definitions = get_shortcode_definitions(store)
    result = text

    for _ in range(MAX_PASSES):
        changed = False

        def replace_self(match: re.Match) -> str:
            nonlocal changed
            name = match.group("name")
            meta = definitions.get(name)
            if not meta or not meta.get("is_self_closing"):
                return match.group(0)
            attrs = parse_attrs(match.group("attrs"))
            ctx = {**attrs, "content": ""}
            changed = True
            return _render_template(meta["html_template"], ctx)

        def replace_pair(match: re.Match) -> str:
            nonlocal changed
            name = match.group("name")
            meta = definitions.get(name)
            if not meta or meta.get("is_self_closing"):
                return match.group(0)
            attrs = parse_attrs(match.group("attrs"))
            ctx = {**attrs, "content": match.group("body")}
            changed = True
            return _render_template(meta["html_template"], ctx)

        # Self-closing first, then innermost pairs (repeat until stable)
        new_result = _SELF_RE.sub(replace_self, result)
        new_result = _PAIR_RE.sub(replace_pair, new_result)
        if new_result == result:
            break
        result = new_result

    return result


def list_shortcodes_for_admin(store) -> list[dict[str, Any]]:
    """Builtin + custom shortcodes for editor UI."""
    defs = get_shortcode_definitions(store)
    items = []
    for name, meta in sorted(defs.items(), key=lambda x: x[0]):
        items.append(
            {
                "id": meta.get("id"),
                "name": name,
                "label": meta.get("label") or name,
                "description": meta.get("description") or "",
                "is_self_closing": bool(meta.get("is_self_closing")),
                "html_template": meta.get("html_template") or "",
                "example": meta.get("example") or "",
                "is_system": bool(meta.get("is_system")),
                "is_active": True,
            }
        )
    return items
