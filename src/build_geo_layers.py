"""Turn three real GIS source files into the embed-ready JSON blobs used by
../demo/civic-blvd-heatmap.html: district boundaries, MRT track geometry,
road-surface polygons, and geometric road intersections.

None of the source files are stored in this repo (they were supplied
directly by a user in conversation, not fetched over the network). Point
this script at your own copies to regenerate the demo's data layers, e.g.
after getting an updated shapefile or extending the study radius.

Inputs (all in TWD97 / EPSG:3826 unless noted):
  --districts   TopoJSON of Taiwan administrative boundaries (e.g. a
                "taiwan towns" file at any scale) -- WGS84 lon/lat, no
                reprojection needed for this one.
  --mrt-lines   GeoJSON FeatureCollection of MRT route centerlines, with a
                "RouteName" property per feature (LineString/MultiLineString).
  --roads       Path to a road shapefile's .shp file (its .dbf/.shx/.prj
                siblings must sit next to it). Expects ROADNAME and
                ROADWIDTH fields; geometry is expected to be road-surface
                polygons (not bare centerlines), as Taiwan's "8m+ road"
                cadastral layers typically are.

Output: five JSON files (districts.json, mrt_lines.json, roads.json,
civic_road.json, intersections.json) written to --out-dir, each already in
the local km-offset coordinate system centered on --center-lat/--center-lon
that civic-blvd-heatmap.html expects. Paste their contents into that file's
DISTRICTS/MRT_LINES/ROADS/CIVIC_ROAD/CROSSING_SITES constants.

Requires: pip install pyshp pyproj
"""

import argparse
import json
import math
import re
from collections import defaultdict
from itertools import combinations

import shapefile
from pyproj import Transformer

LINE_GROUP_COLOR_BY_NAME = {
    "淡水線": "red", "信義線": "red", "信義線東延段": "red",
    "新店線": "green", "碧潭支線": "green", "松山線": "green",
    "中和線": "orange", "蘆洲線": "orange", "新莊線": "orange", "小南門線": "orange",
    "板橋線": "blue", "南港線": "blue",
    "木柵線": "brown", "內湖線": "brown",
    "環狀線": "yellow",
}

# Named roads used for both the general road layer and geometric
# intersection detection. Extend this if you widen the study radius.
CURATED_ROADS = [
    "市民大道一段", "鄭州路", "中山北路一段", "中山北路二段",
    "重慶北路一段", "重慶北路二段", "延平北路一段", "延平北路二段",
    "忠孝西路一段", "忠孝東路一段", "環河北路一段", "南京西路",
    "民權西路", "民生西路", "新生北路一段", "新生北路二段", "新生北路三段",
]


def project_factory(center_lat, center_lon):
    lat_rad = math.radians(center_lat)

    def project(lon, lat):
        x = (lon - center_lon) * 111.320 * math.cos(lat_rad)
        y = (center_lat - lat) * 110.574
        return (round(x, 4), round(y, 4))

    return project


def simplify(points, eps_km):
    if not points:
        return points
    out = [points[0]]
    for p in points[1:]:
        last = out[-1]
        if math.hypot(p[0] - last[0], p[1] - last[1]) >= eps_km:
            out.append(p)
    if out[-1] != points[-1]:
        out.append(points[-1])
    return out


def clip_runs(points, radius_km):
    """Split a polyline into runs within radius_km of the origin, each
    padded by one point on either side so the clipped line still reaches
    the edge of the visible circle instead of stopping short."""
    runs, current, inside_prev = [], [], False
    for i, pt in enumerate(points):
        is_in = math.hypot(*pt) <= radius_km
        if is_in:
            if not current and i > 0 and not inside_prev:
                current.append(points[i - 1])
            current.append(pt)
        else:
            if current:
                current.append(pt)
                runs.append(current)
                current = []
        inside_prev = is_in
    if current:
        runs.append(current)
    return [r for r in runs if len(r) >= 2]


def build_districts(path, project, keep_radius_km, drop_names=()):
    with open(path, encoding="utf-8") as f:
        topo = json.load(f)
    transform = topo["transform"]
    scale, translate = transform["scale"], transform["translate"]

    def decode_arc(arc):
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((translate[0] + x * scale[0], translate[1] + y * scale[1]))
        return pts

    def get_arc(i):
        return decode_arc(topo["arcs"][i]) if i >= 0 else list(reversed(decode_arc(topo["arcs"][~i])))

    def ring_coords(arc_idxs):
        coords = []
        for idx in arc_idxs:
            pts = get_arc(idx)
            coords.extend(pts[1:] if coords and coords[-1] == pts[0] else pts)
        return coords

    out = {}
    for g in topo["objects"][list(topo["objects"].keys())[0]]["geometries"]:
        name = g["properties"].get("name") or g["properties"].get("NAME") or str(g.get("id"))
        if name in drop_names:
            continue
        ring = ring_coords(g["arcs"][0])
        proj_ring = [list(project(lon, lat)) for lon, lat in ring]
        min_d = min(math.hypot(*p) for p in proj_ring)
        if min_d > keep_radius_km:
            continue  # polygon doesn't reach anywhere near the study area
        cx = sum(p[0] for p in proj_ring) / len(proj_ring)
        cy = sum(p[1] for p in proj_ring) / len(proj_ring)
        label_dist = math.hypot(cx, cy)
        label_clamp = keep_radius_km * 0.85
        if label_dist > label_clamp:
            f = label_clamp / label_dist
            cx, cy = cx * f, cy * f
        out[name] = {"ring": proj_ring, "label": [round(cx, 3), round(cy, 3)]}
    return out


def build_mrt_lines(path, to_wgs84, project, keep_radius_km):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for feat in data["features"]:
        name = feat["properties"]["RouteName"]
        color = LINE_GROUP_COLOR_BY_NAME.get(name, "gray")
        geom = feat["geometry"]
        parts = geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]
        for part in parts:
            pts_km = [project(*to_wgs84.transform(x, y)) for x, y in part]
            for run in clip_runs(pts_km, keep_radius_km):
                out.append({"name": name, "color": color, "path": run})
    return out


def build_roads(shp_path, to_twd97, to_wgs84, project, center_m, bbox_radius_m, keep_radius_km, simplify_km):
    sf = shapefile.Reader(shp_path)
    cx_m, cy_m = center_m
    kept = []
    for i in range(len(sf)):
        shp = sf.shape(i)
        bx0, by0, bx1, by1 = shp.bbox
        if (bx1 < cx_m - bbox_radius_m or bx0 > cx_m + bbox_radius_m
                or by1 < cy_m - bbox_radius_m or by0 > cy_m + bbox_radius_m):
            continue
        rec = sf.record(i)
        name = (rec["ROADNAME"] or "").strip()
        width = rec["ROADWIDTH"]
        parts_idx = list(shp.parts) + [len(shp.points)]
        rings_km, min_d = [], float("inf")
        for pi in range(len(parts_idx) - 1):
            seg = shp.points[parts_idx[pi]:parts_idx[pi + 1]]
            ring_km = []
            for x, y in seg:
                px, py = project(*to_wgs84.transform(x, y))
                ring_km.append((px, py))
                min_d = min(min_d, math.hypot(px, py))
            rings_km.append(ring_km)
        if min_d > keep_radius_km:
            continue
        kept.append({
            "name": name,
            "width": round(width, 1) if width else 0,
            "rings": [simplify(r, simplify_km) for r in rings_km],
        })
    return kept


def find_intersections(roads):
    pts_by_name = defaultdict(list)
    for r in roads:
        if r["name"] in CURATED_ROADS:
            for ring in r["rings"]:
                pts_by_name[r["name"]].extend(ring)

    def base_name(n):
        return re.sub(r"(一|二|三|四|五|六|七|八)段$", "", n)

    exclude_pairs = {frozenset(["市民大道一段", "鄭州路"])}
    threshold_km = 0.045
    found = []
    names = [n for n in CURATED_ROADS if pts_by_name.get(n)]
    for a, b in combinations(names, 2):
        if base_name(a) == base_name(b) or frozenset([a, b]) in exclude_pairs:
            continue
        best = min(
            ((math.hypot(p[0] - q[0], p[1] - q[1]), p, q) for p in pts_by_name[a] for q in pts_by_name[b]),
            default=(float("inf"), None, None),
        )
        if best[0] <= threshold_km:
            mx, my = (best[1][0] + best[2][0]) / 2, (best[1][1] + best[2][1]) / 2
            found.append({"name": f"{base_name(a)}×{base_name(b)}", "x": round(mx, 3), "y": round(my, 3)})

    # merge near-duplicate points sharing the same label
    merged, used = [], [False] * len(found)
    for i, a in enumerate(found):
        if used[i]:
            continue
        group = [a]
        used[i] = True
        for j in range(i + 1, len(found)):
            b = found[j]
            if not used[j] and a["name"] == b["name"] and math.hypot(a["x"] - b["x"], a["y"] - b["y"]) < 0.02:
                group.append(b)
                used[j] = True
        merged.append({
            "name": a["name"],
            "x": round(sum(g["x"] for g in group) / len(group), 3),
            "y": round(sum(g["y"] for g in group) / len(group), 3),
        })
    return merged


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--districts", required=True, help="path to district-boundary TopoJSON")
    ap.add_argument("--mrt-lines", required=True, help="path to MRT route GeoJSON (EPSG:3826)")
    ap.add_argument("--roads", required=True, help="path to road shapefile .shp (EPSG:3826)")
    ap.add_argument("--center-lat", type=float, default=25.0485)
    ap.add_argument("--center-lon", type=float, default=121.5187)
    ap.add_argument("--radius-km", type=float, default=2.75, help="visible view radius")
    ap.add_argument("--clip-radius-km", type=float, default=3.3, help="data clip radius (should exceed --radius-km)")
    ap.add_argument("--simplify-km", type=float, default=0.006, help="min vertex spacing after simplification")
    ap.add_argument("--out-dir", default="../data/geo")
    args = ap.parse_args()

    import os
    os.makedirs(args.out_dir, exist_ok=True)

    project = project_factory(args.center_lat, args.center_lon)
    to_wgs84 = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
    to_twd97 = Transformer.from_crs("EPSG:4326", "EPSG:3826", always_xy=True)
    center_m = to_twd97.transform(args.center_lon, args.center_lat)

    districts = build_districts(args.districts, project, keep_radius_km=args.clip_radius_km)
    mrt_lines = build_mrt_lines(args.mrt_lines, to_wgs84, project, args.clip_radius_km)
    roads = build_roads(
        args.roads, to_twd97, to_wgs84, project, center_m,
        bbox_radius_m=args.clip_radius_km * 1000, keep_radius_km=args.radius_km + 0.15,
        simplify_km=args.simplify_km,
    )
    civic_segments = [r for r in roads if r["name"] in ("市民大道一段", "鄭州路")]
    civic_only_pts = [p for r in civic_segments if r["name"] == "市民大道一段" for ring in r["rings"] for p in ring]
    civic_label = [round(sum(p[0] for p in civic_only_pts) / len(civic_only_pts), 3),
                   round(sum(p[1] for p in civic_only_pts) / len(civic_only_pts), 3)] if civic_only_pts else [0, 0]
    intersections = find_intersections(roads)

    outputs = {
        "districts.json": districts,
        "mrt_lines.json": mrt_lines,
        "roads.json": roads,
        "civic_road.json": {"segments": civic_segments, "label": civic_label},
        "intersections.json": intersections,
    }
    for filename, payload in outputs.items():
        path = os.path.join(args.out_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        print(f"wrote {path} ({os.path.getsize(path):,} bytes)")


if __name__ == "__main__":
    main()
