"""④ 找出基地附近所有可能大量聚集人潮的地點並標記出功能與用途。

資料涵蓋範圍(講清楚哪些有、哪些沒有,不用演算法猜):
- ✅ 捷運站點位(有座標+站名)+ 各站歷年進出站人次(可用站名對應,但人次資料沒有
  切到「站內 vs 站外」,也沒有時段細分,只有年度加總)
- ✅ 即時停車場位置(車位數可作為間接指標,但不是人潮本身)
- ✅ 都市計畫分區裡的「市場用地」「機關用地」「文教區」「國小/國中/大專用地」
  (這些用地類型通常伴隨人潮聚集,但分區本身不代表現況真的人潮多)
- ❌ 完全沒有:百貨公司、夜市、宗教場所、體育館、里民活動中心等實際 POI 名單
  （這些不在分區資料裡,分區只會寫「商業區」,不會告訴你裡面是不是百貨公司）
- ❌ 沒有公車站牌資料

以下只标注「已知且有資料佐證」的聚集地點類型與位置,商業區/住宅區本身不當作
「聚集地點」處理,只有市場用地、機關用地、文教設施用地、捷運站、停車場才列入。
"""

import csv
import json
import os

from clip_utils import clip_features_3826, clip_points_xy
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_geojson, load_shapefile_as_geojson

CROWD_ZONING_CATEGORIES = {
    "市場用地": "市場",
    "機關用地": "公家機關",
    "文教區": "文教設施",
    "國小用地": "國小",
    "國中用地": "國中",
    "高中用地": "高中",
    "大專用地": "大專院校",
    "體育場用地": "體育場館",
    "行政區": "行政機關",
}


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # -- MRT 站點 + 進出站人次 --
    stations = load_geojson(os.path.join(RAW_DIR, "mrt_stations.json"))
    stations_in_site = clip_features_3826(stations["features"])

    ridership_by_station_latest_year = {}
    with open(os.path.join(RAW_DIR, "mrt_ridership_by_station_year.csv"), encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["捷運站別"]
            year = row["統計期"]
            year_num = int(year.rstrip("年")) if year.rstrip("年").isdigit() else -1
            try:
                total = int(row["進站人次"]) + int(row["出站人次"])
            except ValueError:
                continue
            prev = ridership_by_station_latest_year.get(name)
            if prev is None or year_num > prev[0]:
                ridership_by_station_latest_year[name] = (year_num, year, total)

    station_summary = []
    for f in stations_in_site:
        name = f["properties"]["NAME"]
        # 站名對照:捷運站點位資料的站名常帶「站」字尾，人次資料多半沒有
        lookup_name = name[:-1] if name.endswith("站") else name
        ridership = ridership_by_station_latest_year.get(name) or ridership_by_station_latest_year.get(lookup_name)
        station_summary.append(
            {
                "name": name,
                "loc": f["properties"].get("LOC"),
                "latest_ridership_year": ridership[1] if ridership else None,
                "latest_ridership_total_entries_exits": ridership[2] if ridership else None,
            }
        )
    station_summary.sort(key=lambda s: -(s["latest_ridership_total_entries_exits"] or 0))

    with open(os.path.join(PROCESSED_DIR, "mrt_stations_clipped.geojson"), "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": stations_in_site}, f, ensure_ascii=False)

    # -- 停車場 --
    parking = load_geojson(os.path.join(RAW_DIR, "parking_lots_live.json"))
    parking_records = []
    for p in parking["data"]["park"]:
        try:
            x, y = float(p["tw97x"]), float(p["tw97y"])
        except (KeyError, TypeError, ValueError):
            continue
        p["_x"], p["_y"] = x, y
        parking_records.append(p)
    parking_in_site = clip_points_xy(parking_records, "_x", "_y")
    total_car_spaces_in_site = sum(p.get("totalcar", 0) or 0 for p in parking_in_site)

    # -- 都市計畫分區裡的人潮聚集用地類型 --
    from shapely.geometry import shape as _shape

    crowd_zoning = {}
    for label, shp in [("主計畫", "主計圖-面.shp"), ("細部計畫", "細計-面.shp")]:
        d = load_shapefile_as_geojson(os.path.join(RAW_DIR, "shp", shp))
        feats = [f for f in d["features"] if f["properties"].get("使用分區") in CROWD_ZONING_CATEGORIES]
        clipped = clip_features_3826(feats)
        by_cat = {}
        for f in clipped:
            cat = f["properties"]["使用分區"]
            by_cat.setdefault(cat, {"features": 0, "area_m2": 0.0})
            by_cat[cat]["features"] += 1
            by_cat[cat]["area_m2"] += _shape(f["geometry"]).area
        for cat in by_cat:
            by_cat[cat]["area_m2"] = round(by_cat[cat]["area_m2"], 1)
        crowd_zoning[label] = by_cat
        out_path = os.path.join(PROCESSED_DIR, f"crowd_zoning_{label}_clipped.geojson")
        with open(out_path, "w", encoding="utf-8") as fo:
            json.dump({"type": "FeatureCollection", "features": clipped}, fo, ensure_ascii=False)

    result = {
        "CAVEAT": (
            "沒有百貨/夜市/宗教場所/體育館等實際 POI 名單，也沒有公車站牌資料。"
            "以下只列出有資料佐證的聚集地點類型：捷運站、停車場、市場用地、機關/文教/學校用地分區。"
        ),
        "mrt_stations_in_site": station_summary,
        "parking": {
            "lots_in_site": len(parking_in_site),
            "total_car_spaces_in_site": total_car_spaces_in_site,
        },
        "crowd_related_zoning_by_source": crowd_zoning,
        "zoning_category_meaning": CROWD_ZONING_CATEGORIES,
    }
    with open(os.path.join(PROCESSED_DIR, "analysis4_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
