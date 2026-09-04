"""⑨ 用建築量體對地標,assume 商業活動,呈現公園周圍活動密度(含 PR25 以下公園對照)。

做法(先講清楚假設跟限制):
- 「建築輪廓對地標」= 把 analysis8 的真實 OSM POI(餐飲/零售/辦公室,不含公園綠地
  tag)配對到最近的建築量體(buildings_clipped.geojson,使用者提供的 3D 建物圖磚,
  EPSG:3826)。配對規則:POI 落在某棟建築外緣 ASSUME_RADIUS_M(15公尺)緩衝範圍內
  才算,若同時落入多棟緩衝範圍,指派給距離最近的那棟。這是**空間鄰近的假設**,
  不是「這間店真的登記在這棟建築」的實際商業登記資料——狹窄巷弄或高密度街廓
  可能配對到相鄰棟而非正確棟。
- 這樣算出的是「某棟建築附近有幾個真實 OSM 商業/辦公 POI」,拿來當作該建築商業
  活動密度的代理值(activity_poi_count),不是實際營業額或人流。
- **建築量體資料涵蓋率不是100%**:buildings_clipped.geojson 是使用者陸續上傳的
  多個圖磚拼接而成,不保證涵蓋整個基地——用 20x20 網格粗略檢查,基地邊界範圍內
  約 80% 網格至少有1棟建築,其餘 20% 可能是真的開放空間(公園/綠地/水岸/道路),
  也可能是圖磚沒涵蓋到的資料缺口,兩者從這份資料本身無法區分,不能直接當作
  「零商業活動」。所以下面每座公園的統計都同時報告
  buildings_with_tile_coverage_within_400m(400m內有建築圖磚資料的棟數),数值
  偏低時要說明可能是資料缺口,不是真的沒建築。
- OSM POI 本身也不保證100%涵蓋(見 analysis8 CAVEAT),辦公室尤其可能低估。
- POI 落在任何建築 15m 緩衝範圍外 = 配對不到,計入 unmatched_poi_count,不會消失
  不報告。
"""

import json
import os

from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from config import PROCESSED_DIR
from gis_utils import load_geojson, wgs84_to_proj

ASSUME_RADIUS_M = 15
COMMERCIAL_CATEGORIES = {"餐飲", "零售/商店", "辦公室"}
PARK_RADIUS_M = 400


def main():
    buildings = load_geojson(os.path.join(PROCESSED_DIR, "buildings_clipped.geojson"))["features"]
    building_geoms = [shape(f["geometry"]) for f in buildings]
    buffered_geoms = [g.buffer(ASSUME_RADIUS_M) for g in building_geoms]
    tree = STRtree(buffered_geoms)

    osm_poi = load_geojson(os.path.join(PROCESSED_DIR, "osm_poi_clipped.geojson"))["features"]

    counts = [{"activity_poi_count": 0, "餐飲": 0, "零售/商店": 0, "辦公室": 0} for _ in building_geoms]
    matched_poi_count = 0
    unmatched_poi_count = 0

    for f in osm_poi:
        cats = [c for c in f["properties"].get("categories", []) if c in COMMERCIAL_CATEGORIES]
        if not cats:
            continue
        lon, lat = f["geometry"]["coordinates"]
        x, y = wgs84_to_proj(lon, lat)
        pt = Point(x, y)

        candidates = [i for i in tree.query(pt) if buffered_geoms[i].contains(pt)]
        if not candidates:
            unmatched_poi_count += 1
            continue
        best = min(candidates, key=lambda i: building_geoms[i].distance(pt))
        matched_poi_count += 1
        counts[best]["activity_poi_count"] += 1
        for c in cats:
            counts[best][c] += 1

    activity_features = []
    for f, g, c in zip(buildings, building_geoms, counts):
        activity_features.append(
            {
                "type": "Feature",
                "geometry": f["geometry"],
                "properties": {
                    "height": f["properties"].get("height"),
                    "activity_poi_count": c["activity_poi_count"],
                    "dining_poi_count": c["餐飲"],
                    "retail_poi_count": c["零售/商店"],
                    "office_poi_count": c["辦公室"],
                },
            }
        )

    with open(os.path.join(PROCESSED_DIR, "buildings_activity.geojson"), "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": activity_features}, f, ensure_ascii=False)

    # -- 逐公園統計 400m 內建築活動密度,順便標出建築圖磚涵蓋率過低(資料缺口)的公園 --
    parks_geo = load_geojson(os.path.join(PROCESSED_DIR, "parks_basic_info_clipped.geojson"))["features"]
    analysis7 = json.load(open(os.path.join(PROCESSED_DIR, "analysis7_summary.json"), encoding="utf-8"))
    low_connectivity_names = {p["name"] for p in analysis7["low_connectivity_parks_pr25_below"]}

    building_centroids = [g.centroid for g in building_geoms]
    centroid_tree = STRtree(building_centroids)

    park_activity = []
    for f in parks_geo:
        name = f["properties"].get("pm_name")
        lon, lat = f["geometry"]["coordinates"]
        x, y = wgs84_to_proj(lon, lat)
        center = Point(x, y)
        buf = center.buffer(PARK_RADIUS_M)

        idxs = [i for i in centroid_tree.query(buf) if buf.contains(building_centroids[i])]
        n_buildings = len(idxs)
        total_activity = sum(counts[i]["activity_poi_count"] for i in idxs)
        avg_activity = round(total_activity / n_buildings, 2) if n_buildings else None

        park_activity.append(
            {
                "name": name,
                "low_connectivity_pr25_below": name in low_connectivity_names,
                "buildings_with_tile_coverage_within_400m": n_buildings,
                "total_activity_poi_within_400m": total_activity,
                "avg_activity_poi_per_building_within_400m": avg_activity,
            }
        )

    def group_stats(records):
        vals = [r["avg_activity_poi_per_building_within_400m"] for r in records if r["avg_activity_poi_per_building_within_400m"] is not None]
        cov = [r["buildings_with_tile_coverage_within_400m"] for r in records]
        return {
            "park_count": len(records),
            "park_count_with_building_data": len(vals),
            "avg_activity_poi_per_building": round(sum(vals) / len(vals), 2) if vals else None,
            "avg_buildings_with_tile_coverage_within_400m": round(sum(cov) / len(cov), 1) if cov else None,
        }

    low_group = [r for r in park_activity if r["low_connectivity_pr25_below"]]
    rest_group = [r for r in park_activity if not r["low_connectivity_pr25_below"]]

    low_coverage_gap_parks = sorted(
        [r for r in park_activity if r["buildings_with_tile_coverage_within_400m"] < 5],
        key=lambda r: r["buildings_with_tile_coverage_within_400m"],
    )

    result = {
        "CAVEAT": (
            "activity_poi_count 是「15m內最近的真實OSM商業/辦公POI數」的空間鄰近代理值,"
            "不是實際商業登記或人流資料;buildings_with_tile_coverage_within_400m 低"
            "不代表該公園周圍真的沒建築/沒商業,很可能是使用者上傳的建築圖磚沒涵蓋到"
            "那個位置(圖磚是陸續拼接的,基地內約20%網格目前沒有建築資料),兩種情況"
            "在這份資料裡無法區分,已在 low_building_tile_coverage_parks 裡個別列出,"
            "解讀「活動密度低」的公園時要先排除這些資料缺口的公園,不能直接當成"
            "「這裡本來就沒有活動聚集」。"
        ),
        "assume_radius_m": ASSUME_RADIUS_M,
        "park_radius_m": PARK_RADIUS_M,
        "total_buildings": len(building_geoms),
        "matched_poi_count": matched_poi_count,
        "unmatched_poi_count": unmatched_poi_count,
        "unmatched_poi_note": f"OSM POI 離最近建築超過 {ASSUME_RADIUS_M}m,無法配對到任何建築量體(可能在開放空間/圖磚缺口/建築圖磚本身位置誤差)。",
        "low_connectivity_pr25_group": group_stats(low_group),
        "other_parks_group": group_stats(rest_group),
        "low_building_tile_coverage_parks": [
            {
                "name": r["name"],
                "low_connectivity_pr25_below": r["low_connectivity_pr25_below"],
                "buildings_with_tile_coverage_within_400m": r["buildings_with_tile_coverage_within_400m"],
            }
            for r in low_coverage_gap_parks
        ],
        "park_activity_details": sorted(
            park_activity,
            key=lambda r: (r["avg_activity_poi_per_building_within_400m"] is None, r["avg_activity_poi_per_building_within_400m"] or 0),
        ),
    }
    with open(os.path.join(PROCESSED_DIR, "analysis9_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"buildings: {len(building_geoms)}, matched POI: {matched_poi_count}, unmatched POI: {unmatched_poi_count}")
    print(f"PR25以下公園({len(low_group)}座)周圍建築平均活動POI數:", group_stats(low_group))
    print(f"其餘公園({len(rest_group)}座)周圍建築平均活動POI數:", group_stats(rest_group))
    print(f"建築圖磚資料缺口疑慮的公園(400m內<5棟有資料):{len(low_coverage_gap_parks)} 座")


if __name__ == "__main__":
    main()
