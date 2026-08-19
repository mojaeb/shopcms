"""Shipping distance calculators.

Two strategies:
- haversine_km  : straight-line (as-the-crow-flies) using Haversine formula.
- real_distance_km : road distance via an external routing API with fallback to haversine.

Results are cached with Django's cache framework (key: distance_{store_id}_{lat1}_{lng1}_{lat2}_{lng2},
timeout 30 days) so repeated checkout calculations for the same pair are free.
"""

from __future__ import annotations

import json
import logging
import math
import urllib.error
import urllib.request
from decimal import Decimal

from django.core.cache import cache

logger = logging.getLogger(__name__)

_EARTH_RADIUS_KM = 6371.0
_CACHE_TIMEOUT = 60 * 60 * 24 * 30  # 30 days


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> Decimal:
    """Straight-line distance (km) between two WGS-84 coordinates using Haversine."""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return Decimal(str(round(_EARTH_RADIUS_KM * c, 3)))


def real_distance_km(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
    api_key: str = "",
    store_id: int = 0,
) -> Decimal:
    """Road distance (km) via external routing API with haversine fallback.

    Cache key: distance_{store_id}_{lat1}_{lng1}_{lat2}_{lng2}

    TODO (نیاز به تایید مستندات رسمی):
    ──────────────────────────────────
    سرویس مسیریابی انتخابی باید یکی از این‌ها باشد:
      • OpenRouteService  (https://openrouteservice.org/dev/#/api-docs/v2/directions)
        endpoint: POST https://api.openrouteservice.org/v2/directions/driving-car
        body: {"coordinates": [[lng1, lat1], [lng2, lat2]]}
        header: Authorization: <api_key>
        response: summary.distance (متر) → تقسیم بر ۱۰۰۰ برای کیلومتر

      • نشان‌مپ ایران  (https://map.ir/api/direction)
        header: Api-Key: <api_key>
        قالب request/response از مستندات رسمی api.neshan.org یا map.ir بررسی شود.

    Rate limit، خطاهای ۴۲۹ و سایر محدودیت‌های هر سرویس باید از مستندات رسمی تایید شود.
    تا زمان پیاده‌سازی نهایی، تابع به haversine_km fallback می‌کند.
    ──────────────────────────────────
    """
    # Normalise precision for cache key
    _k = lambda v: round(float(v), 6)
    cache_key = f"distance_{store_id}_{_k(lat1)}_{_k(lng1)}_{_k(lat2)}_{_k(lng2)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return Decimal(str(cached))

    result: Decimal | None = None

    if api_key:
        result = _call_routing_api(lat1, lng1, lat2, lng2, api_key)

    if result is None:
        result = haversine_km(lat1, lng1, lat2, lng2)

    cache.set(cache_key, float(result), timeout=_CACHE_TIMEOUT)
    return result


def _call_routing_api(
    lat1: float, lng1: float, lat2: float, lng2: float, api_key: str
) -> Decimal | None:
    """Attempt an HTTP call to the routing API.

    TODO: پس از تعیین سرویس مسیریابی، endpoint، header ها و پارامترهای request/response را اینجا پیاده کن.
    فعلاً None برمی‌گرداند تا fallback به haversine فعال بماند.
    """
    # Placeholder — routing API not yet configured.
    # Example skeleton for OpenRouteService (uncomment + complete after reviewing their docs):
    #
    # url = "https://api.openrouteservice.org/v2/directions/driving-car"
    # payload = json.dumps({"coordinates": [[lng1, lat1], [lng2, lat2]]}).encode()
    # req = urllib.request.Request(url, data=payload, headers={
    #     "Content-Type": "application/json",
    #     "Authorization": api_key,
    # }, method="POST")
    # try:
    #     with urllib.request.urlopen(req, timeout=10) as resp:
    #         data = json.loads(resp.read())
    #     metres = data["routes"][0]["summary"]["distance"]
    #     return Decimal(str(round(metres / 1000, 3)))
    # except Exception as exc:
    #     logger.warning("Routing API error: %s", exc)
    #     return None

    return None
