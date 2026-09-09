"""Build an Overpass QL `poly` query for a buffer that hugs the real,
curving centerline of 市民大道 (instead of a rectangle that bulges away from
the road wherever it bends) -- so a follow-up POI query can stay "just the
two blocks along the road" for the entire length to 松山車站, not just near
市民大道一段.

Centerline source: ONLY the 市民大道高架道路 (elevated expressway) segments in
../data/mingsheng_road.geojson, since it's the one continuous physical
structure spanning nearly the whole corridor (see filter_road_segments.py
for why ramps/lanes/alleys are excluded from that file already) and its
points are verifiably monotonic west->east once binned. Ways come back
from Overpass as separate unordered segments, so this script does NOT
attempt to chain them end-to-end into one polyline -- it bins every
elevated-segment point by longitude and averages the latitude per bin,
which gives a smoothed west-to-east centerline accurate to roughly one bin
width. That is a real approximation, not a hidden one: BIN_WIDTH_DEG below
controls it, and it is stated again in the printed output.

KNOWN GAP: the elevated deck ends around lon 121.5634 (near 塔悠路), about
700m short of 松山車站. The at-grade 市民大道五段 beyond that point is split
across several disconnected OSM way fragments that a longitude-binned
average cannot safely stitch into one line (a naive attempt produced a
self-crossing polygon -- tried and reverted, not silently worked around).
Properly chaining those fragments needs real line-merge logic (e.g.
shapely.ops.linemerge on matched endpoints), which isn't worth adding as a
dependency for 700m of straight, low-ambiguity street. This script's
corridor buffer simply stops at the elevated deck's east end; that last
stretch needs its own plain bounding-box query if you want it covered too.

Run: python build_corridor_query.py
Prints: the Overpass QL query (poly filter) to stdout, and writes it to
        ../output/corridor_query.txt
Also writes ../data/corridor_polygon.json (the raw north/south vertex
lon/lat arrays) -- re-run build_road_overlay.py afterward to draw this
buffer band on top of the real road map, so you can eyeball the corridor
before spending an Overpass query on it.
"""

import json
import math

IN_PATH = "../data/mingsheng_road.geojson"
QUERY_OUT_PATH = "../output/corridor_query.txt"

BUFFER_M = 300.0
BIN_WIDTH_DEG = 0.0005  # ~50m of longitude at this latitude
METERS_PER_DEG_LAT = 111320.0

# 環河北路 -- the perpendicular offset at the very first centerline point is
# noisy (the ramp merge just west of here makes the local heading wiggle),
# and it stretched the buffer polygon ~200m further west than the road
# itself, i.e. toward/into the river. Clamp instead of leaving that in
# silently: nothing in the corridor should sit west of 環河北路.
WEST_CLAMP_LON = 121.503


def load_centerline_points():
    with open(IN_PATH, encoding="utf-8") as f:
        gj = json.load(f)

    return [
        (lon, lat)
        for ft in gj["features"]
        if ft["properties"].get("name") == "市民大道高架道路"
        for lon, lat in ft["geometry"]["coordinates"]
    ]


def smooth_centerline(points):
    lon_min = min(p[0] for p in points)
    lon_max = max(p[0] for p in points)
    n_bins = max(1, int((lon_max - lon_min) / BIN_WIDTH_DEG) + 1)

    bins = [[] for _ in range(n_bins)]
    for lon, lat in points:
        idx = min(n_bins - 1, int((lon - lon_min) / BIN_WIDTH_DEG))
        bins[idx].append(lat)

    centerline = []
    for i, b in enumerate(bins):
        if not b:
            continue
        lon = lon_min + (i + 0.5) * BIN_WIDTH_DEG
        lat = sum(b) / len(b)
        centerline.append((lon, lat))
    return centerline


def offset_polygon(centerline, buffer_m):
    """Return (north_side_points, south_side_points), each a lon/lat list,
    offset perpendicular to the local heading by buffer_m."""
    north, south = [], []
    n = len(centerline)
    for i, (lon, lat) in enumerate(centerline):
        prev_pt = centerline[i - 1] if i > 0 else centerline[i]
        next_pt = centerline[i + 1] if i < n - 1 else centerline[i]
        cos_lat = math.cos(math.radians(lat))

        dx = (next_pt[0] - prev_pt[0]) * cos_lat  # local "meters-equivalent" units
        dy = next_pt[1] - prev_pt[1]
        seg_len = math.hypot(dx, dy) or 1e-9
        # perpendicular unit vector (rotate heading by 90deg)
        perp_x, perp_y = -dy / seg_len, dx / seg_len

        dlon = (perp_x * buffer_m / METERS_PER_DEG_LAT) / cos_lat
        dlat = perp_y * buffer_m / METERS_PER_DEG_LAT

        north.append((max(lon + dlon, WEST_CLAMP_LON), lat + dlat))
        south.append((max(lon - dlon, WEST_CLAMP_LON), lat - dlat))
    return north, south


def to_overpass_poly(north, south):
    ring = north + list(reversed(south))
    return " ".join(f"{lat:.6f} {lon:.6f}" for lon, lat in ring)


def main():
    elevated_pts = load_centerline_points()
    centerline = smooth_centerline(elevated_pts)
    lons = [c[0] for c in centerline]
    assert all(lons[i] < lons[i + 1] for i in range(len(lons) - 1)), (
        "centerline is not monotonic west->east -- refusing to build a poly "
        "filter from it, since that risks a self-crossing polygon"
    )

    north, south = offset_polygon(centerline, BUFFER_M)
    poly_str = to_overpass_poly(north, south)

    query = f"""[out:json][timeout:90];
(
  node["shop"](poly:"{poly_str}");
  way["shop"](poly:"{poly_str}");
  node["amenity"~"^(restaurant|cafe|fast_food|bar|pub)$"](poly:"{poly_str}");
  way["amenity"~"^(restaurant|cafe|fast_food|bar|pub)$"](poly:"{poly_str}");
  node["office"](poly:"{poly_str}");
  way["office"](poly:"{poly_str}");
);
out center tags;"""

    with open(QUERY_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(query + "\n")

    with open("../data/corridor_polygon.json", "w", encoding="utf-8") as f:
        json.dump({"north": north, "south": south, "buffer_m": BUFFER_M}, f)

    print(f"Centerline: {len(centerline)} smoothed points, lon {lons[0]:.4f} to {lons[-1]:.4f} "
          f"(binned every ~{BIN_WIDTH_DEG*111320*math.cos(math.radians(25.05)):.0f}m of longitude)")
    print(f"Buffer: +/-{BUFFER_M:.0f}m each side, poly has {len(north)+len(south)} vertices")
    print("Covers 環河北路 to the elevated deck's east end (~塔悠路一帶); does NOT "
          "reach 松山車站 -- see the KNOWN GAP note in this file's docstring.")
    print(f"Wrote query to {QUERY_OUT_PATH}\n")
    print(query)


if __name__ == "__main__":
    main()
