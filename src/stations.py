"""Distance filtering helpers."""

import math

from config import CENTER_LAT, CENTER_LON, MRT_STATIONS, RADIUS_KM


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r_km * math.asin(math.sqrt(a))


def stations_in_radius():
    """Return the configured MRT stations that fall within RADIUS_KM of the
    Section-1 centroid, each tagged with its distance in km."""
    result = []
    for s in MRT_STATIONS:
        d = haversine_km(CENTER_LAT, CENTER_LON, s.lat, s.lon)
        if d <= RADIUS_KM:
            result.append((s, d))
    return sorted(result, key=lambda pair: pair[1])


if __name__ == "__main__":
    for s, d in stations_in_radius():
        print(f"{s.name:8s} {d:.2f} km  ({s.lat}, {s.lon})")
