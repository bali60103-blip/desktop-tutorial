"""Fetch the real centerline geometry of 市民大道 (all sections) from
OpenStreetMap via the Overpass API, as GeoJSON.

This is the actual road network -- real lat/lon coordinates traced from
OSM way geometry -- meant to replace any hand-drawn/schematic stand-in for
市民大道's shape. It does NOT fetch land-use, commercial, or population
data; see fetch_mrt_hourly.py / poll_youbike.py for the open-data proxies
used elsewhere in this project, and data_sources.md for what none of this
covers (real land-use/commercial-type/cognitive-map data still has to come
from other sources or original survey work).

NOTE ON VERIFICATION: this script was written from a sandboxed environment
whose network egress policy blocks the Overpass API outright (confirmed via
a direct connection test to overpass-api.de: `CONNECT tunnel failed,
response 403`), so the query below could NOT be exercised end-to-end from
here. Before relying on it:
  1. Optionally paste OVERPASS_QUERY into https://overpass-turbo.eu/ to
     preview what it returns and check nothing unexpected matches.
  2. Run this script from a machine/CI job with normal internet access.

Run: python fetch_road_network.py
Output: ../data/mingsheng_road.geojson -- a GeoJSON FeatureCollection with
        one LineString feature per OSM way segment named 市民大道 (or
        市民大道X段), each carrying its original OSM tags as properties.
"""

import json
import sys

import requests

# Generous bounding box (south, west, north, east) covering all of
# 市民大道's sections (1-7) across Datong / Zhongshan / Songshan / Da'an.
# Widen this if a section is missing from the result.
BBOX = (25.020, 121.480, 25.075, 121.590)

OVERPASS_QUERY = f"""
[out:json][timeout:60];
way["name"~"^市民大道"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
out geom;
""".strip()

# Try the main instance first, then a known mirror if it's unreachable/overloaded.
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

OUT_PATH = "../data/mingsheng_road.geojson"


def fetch_elements():
    last_exc = None
    for url in OVERPASS_ENDPOINTS:
        try:
            resp = requests.post(url, data={"data": OVERPASS_QUERY}, timeout=60)
            resp.raise_for_status()
            return resp.json().get("elements", [])
        except requests.RequestException as exc:
            last_exc = exc
            print(f"{url} failed ({exc}), trying next endpoint...", file=sys.stderr)
    raise last_exc


def to_geojson(elements):
    features = []
    for el in elements:
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in el["geometry"]]
        if len(coords) < 2:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {"osm_id": el["id"], **el.get("tags", {})},
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def main():
    try:
        elements = fetch_elements()
    except requests.RequestException as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        print(
            "If this is a 403/connection error, your network may be blocking "
            "the Overpass API -- this happens inside restricted sandboxes.",
            file=sys.stderr,
        )
        sys.exit(1)

    geojson = to_geojson(elements)
    if not geojson["features"]:
        print(
            "No matching ways -- widen BBOX in this script, or check the "
            "query against https://overpass-turbo.eu/ (name variants can "
            "differ, e.g. missing 段 suffixes).",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(geojson['features'])} way segments to {OUT_PATH}")


if __name__ == "__main__":
    main()
