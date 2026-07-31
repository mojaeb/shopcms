"""Color helpers for product attribute values."""

from __future__ import annotations

import re

_HEX_SPLIT = re.compile(r"[,،/\s]+")


def parse_color_codes(raw: str | None) -> list[str]:
    """Parse one or more color codes from a stored string.

    Accepts: ``#111``, ``#111111,#ffffff``, ``#aaa / #bbb``.
    """
    if not raw:
        return []
    codes: list[str] = []
    for part in _HEX_SPLIT.split(str(raw).strip()):
        token = part.strip()
        if not token:
            continue
        if not token.startswith("#"):
            token = f"#{token}"
        codes.append(token)
    return codes


def normalize_color_code(raw: str | None) -> str:
    """Normalize multi-color input to a comma-separated storage string."""
    return ",".join(parse_color_codes(raw))


def color_swatch_css(raw: str | None) -> str:
    """CSS background value for a swatch (solid or split)."""
    codes = parse_color_codes(raw)
    if not codes:
        return "#cccccc"
    if len(codes) == 1:
        return codes[0]
    stops = []
    n = len(codes)
    for i, code in enumerate(codes):
        start = (i / n) * 100
        end = ((i + 1) / n) * 100
        stops.append(f"{code} {start:.2f}% {end:.2f}%")
    return f"conic-gradient(from 135deg, {', '.join(stops)})"
