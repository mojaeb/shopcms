"""Geographic helper utilities."""

from __future__ import annotations

# Iran bounding box — source: Natural Earth / UN GAUL administrative boundaries.
# lat: 25.078237 (Chabahar area) … 39.777672 (northern border near Aras river)
# lng: 44.032000 (western corner, border with Iraq/Turkey) … 63.317000 (eastern corner, border with Pakistan/Afghanistan)
_IRAN_LAT_MIN = 25.078237
_IRAN_LAT_MAX = 39.777672
_IRAN_LNG_MIN = 44.032000
_IRAN_LNG_MAX = 63.317000


def is_iran_coordinate(lat: float, lng: float) -> bool:
    """Return True if (lat, lng) falls inside Iran's bounding box."""
    return _IRAN_LAT_MIN <= lat <= _IRAN_LAT_MAX and _IRAN_LNG_MIN <= lng <= _IRAN_LNG_MAX
