"""Build the 2km-buffered site corridor along 市民大道西段(西端至華山大草皮)。
延平河濱公園不在此範圍內,見 config.py 說明。

Outputs (in ../data/processed/):
- site_corridor_line.geojson  — 市民大道西段中心線(WGS84,僅供參考/檢查用)
- site_boundary.geojson       — 2km 緩衝範圍面(WGS84,後續各分析用這個裁切資料)
"""

import json
import os

from shapely.geometry import LineString, MultiPoint, mapping
from shapely.ops import transform, unary_union

from config import (
    BUFFER_METERS,
    CORRIDOR_WEST_LAT,
    CORRIDOR_WEST_LON,
    HUASHAN_LAWN_LAT,
    HUASHAN_LAWN_LON,
    PROCESSED_DIR,
    RAW_DIR,
)
from gis_utils import load_geojson, proj_to_wgs84, wgs84_to_proj


def build_corridor_segments():
    """市民大道高架道路(OSM 匯出)裡,西端起點到華山大草皮經度之間的路段。

    每個 OSM way 本身座標順序就是對的(不能跨 way 用經度排序串接,因為同一里程
    常有雙向車道/匝道等多條並行線,經度排序會連出鋸齒狀的假路徑,把緩衝走廊拉得
    過長、形狀也不對)。所以這裡保留每個 feature 自己的線型,個別 buffer 之後再
    unary_union,才是正確的「沿線緩衝走廊」做法。"""
    d = load_geojson(os.path.join(RAW_DIR, "osm_bridges.geojson"))
    lines_wgs84 = []
    for feat in d["features"]:
        if feat["properties"].get("name") != "市民大道高架道路":
            continue
        coords = feat["geometry"]["coordinates"]
        lons = [c[0] for c in coords]
        if max(lons) < CORRIDOR_WEST_LON - 0.002 or min(lons) > HUASHAN_LAWN_LON + 0.01:
            continue
        lines_wgs84.append(coords)
    return lines_wgs84


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    segments_wgs84 = build_corridor_segments()
    if len(segments_wgs84) < 1:
        raise SystemExit("Not enough corridor segments found — check osm_bridges.geojson")

    lines_proj = []
    for coords in segments_wgs84:
        pts_proj = [wgs84_to_proj(lon, lat) for lon, lat in coords]
        lines_proj.append(LineString(pts_proj))
    # also anchor the west/east ends explicitly so the buffer reaches both
    anchor_pts_proj = MultiPoint(
        [
            wgs84_to_proj(CORRIDOR_WEST_LON, CORRIDOR_WEST_LAT),
            wgs84_to_proj(HUASHAN_LAWN_LON, HUASHAN_LAWN_LAT),
        ]
    )

    multiline_proj = unary_union(lines_proj)
    buffer_proj = unary_union(
        [multiline_proj.buffer(BUFFER_METERS), anchor_pts_proj.buffer(BUFFER_METERS)]
    )

    line_wgs84 = transform(lambda x, y: proj_to_wgs84(x, y), multiline_proj)
    buffer_wgs84 = transform(lambda x, y: proj_to_wgs84(x, y), buffer_proj)

    with open(os.path.join(PROCESSED_DIR, "site_corridor_line.geojson"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": mapping(line_wgs84),
                        "properties": {
                            "name": "市民大道西段路廊(延平河濱公園端—華山大草皮,OSM 橋樑路段近似,非完整平面道路)",
                            "length_m": round(multiline_proj.length, 1),
                        },
                    }
                ],
            },
            f,
            ensure_ascii=False,
        )

    with open(os.path.join(PROCESSED_DIR, "site_boundary.geojson"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": mapping(buffer_wgs84),
                        "properties": {
                            "name": f"市民大道西段 {BUFFER_METERS}m 緩衝範圍",
                            "area_km2": round(buffer_proj.area / 1_000_000, 2),
                        },
                    }
                ],
            },
            f,
            ensure_ascii=False,
        )

    print(f"corridor segments used: {len(segments_wgs84)}")
    print(f"corridor total length (sum of segments): {multiline_proj.length/1000:.2f} km")
    print(f"buffer area: {buffer_proj.area/1_000_000:.2f} km2")


if __name__ == "__main__":
    main()
