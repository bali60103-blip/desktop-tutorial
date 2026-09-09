"""Filter a raw Overpass export of `name~"^市民大道"` ways down to the actual
through-road spine: the elevated expressway plus the numbered surface
sections, dropping ramps and the side lanes/alleys that only borrow the
boulevard's name.

Why this is needed: querying OSM for anything named "^市民大道" also matches
on/off ramps (市民大道入口/出口匝道, which peel away from the corridor toward
建國南路/三重 etc.) and small residential lanes/alleys named after the
section they're off of (市民大道三段128巷, 二段67巷, ...). Those aren't the
boulevard itself and would distort a "which side of the road is this POI on"
classification, so they're excluded here rather than left for a human to
eyeball out of a 90-way file.

Keep rule: highway type is trunk/trunk_link/tertiary/tertiary_link AND the
name does not contain 巷, 弄 (lane/alley) or 匝道 (ramp).

Run: python filter_road_segments.py <raw_overpass_export.geojson>
Output: ../data/mingsheng_road.geojson
"""

import json
import sys

OUT_PATH = "../data/mingsheng_road.geojson"

MAIN_HIGHWAY_TYPES = {"trunk", "trunk_link", "tertiary", "tertiary_link"}
EXCLUDE_SUBSTRINGS = ("巷", "弄", "匝道")


def is_main_spine(props):
    name = props.get("name", "")
    if not name.startswith("市民大道"):
        return False
    if any(s in name for s in EXCLUDE_SUBSTRINGS):
        return False
    return props.get("highway") in MAIN_HIGHWAY_TYPES


def main():
    if len(sys.argv) != 2:
        print("Usage: python filter_road_segments.py <raw_overpass_export.geojson>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        gj = json.load(f)

    kept, dropped = [], []
    for ft in gj["features"]:
        (kept if is_main_spine(ft["properties"]) else dropped).append(ft)

    out = {"type": "FeatureCollection", "features": kept}
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Kept {len(kept)} / {len(gj['features'])} ways as the main spine -> {OUT_PATH}")
    dropped_names = sorted({ft["properties"].get("name", "?") for ft in dropped})
    print("Dropped (ramps/lanes/alleys):", ", ".join(dropped_names))


if __name__ == "__main__":
    main()
