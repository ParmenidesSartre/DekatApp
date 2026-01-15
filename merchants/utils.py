from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return r * c


def bounding_box(lat: float, lon: float, radius_km: float) -> tuple[float, float, float, float]:
    # Approximate degrees per km.
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * max(cos(radians(lat)), 0.01))
    return lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta

