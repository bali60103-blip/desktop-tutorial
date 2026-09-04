"""⑦ 依公園設施種類,看周邊 400m 內可能連結的設施/商店與人潮來源。

做法與限制(先講清楚):
- 一般商店(超商、餐飲、服飾等)還是**沒有實際 POI 資料**,商業區/市場用地都市
  計畫分區面積繼續當代理指標,不是店家清單。
- **運動/健身類商家現在有真實 POI 了**(使用者提供,585 筆全市體育署運動產業
  登記資料,含健身房/游泳/體適能/瑜珈/撞球/桌球/武術/舞蹈/市民運動中心等,
  有店名、地址、營業時間、座標),這塊從「分區面積代理」升級成「實際商家清單
  +數量」,尤其對「銀髮健身」「運動場館」這兩個公園設施標籤特別有意義——可以
  直接驗證這類公園附近是不是真的有對應的運動商家聚集,不用再靠分區面積猜。
- 人潮來源用捷運站(含分析④的進出站人次)+ 停車場(車位數)當代理。
- 公園設施種類是從 analysis6 的 pm_sports/pm_recreation 文字裡,用關鍵字比對
  分成幾個粗略類型(銀髮健身/兒童遊戲/運動場館/廣場集會),同一座公園可以同時
  屬於多種類型,不是互斥分類。
"""

import json
import os
from collections import Counter

from shapely.geometry import Point, shape
from shapely.ops import transform

from clip_utils import clip_features_3826
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_geojson, load_shapefile_as_geojson, wgs84_to_proj

RADIUS_M = 400

SENIOR_FITNESS_KW = ["單槓", "轉輪", "扭腰器", "按摩器", "康復器", "漫步機", "伸展", "划船訓練器", "滑雪器"]
CHILD_PLAY_KW = ["組合遊具", "搖搖樂", "翹翹板", "鞦韆", "滑梯", "沙坑", "攀爬"]
SPORTS_VENUE_KW = ["籃球場", "運動場", "游泳池", "網球場", "羽球場", "排球場"]
PLAZA_KW = ["廣場", "音樂臺", "集會"]


def tag_facility_types(park):
    text = " ".join(filter(None, [park.get("sports"), park.get("recreation"), park.get("service")]))
    tags = []
    if any(kw in text for kw in SENIOR_FITNESS_KW):
        tags.append("銀髮健身")
    if any(kw in text for kw in CHILD_PLAY_KW):
        tags.append("兒童遊戲")
    if any(kw in text for kw in SPORTS_VENUE_KW):
        tags.append("運動場館")
    if any(kw in text for kw in PLAZA_KW):
        tags.append("廣場集會")
    return tags or ["其他/未分類"]


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    parks_geo = load_geojson(os.path.join(PROCESSED_DIR, "parks_basic_info_clipped.geojson"))
    park_summary = json.load(open(os.path.join(PROCESSED_DIR, "analysis6_summary.json"), encoding="utf-8"))
    park_info_by_name = {p["name"]: p for p in park_summary["park_list"]}

    stations = load_geojson(os.path.join(RAW_DIR, "mrt_stations.json"))["features"]
    station_geoms = [(shape(f["geometry"]), f["properties"]["NAME"]) for f in stations]

    parking = load_geojson(os.path.join(RAW_DIR, "parking_lots_live.json"))
    parking_pts = []
    for p in parking["data"]["park"]:
        try:
            x, y = float(p["tw97x"]), float(p["tw97y"])
        except (KeyError, TypeError, ValueError):
            continue
        parking_pts.append((Point(x, y), p.get("totalcar", 0) or 0))

    sports_biz = load_geojson(os.path.join(RAW_DIR, "sports_businesses.json"))
    sports_biz_pts = []
    for b in sports_biz:
        try:
            lat, lon = float(b["Latitude"]), float(b["Longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        x, y = wgs84_to_proj(lon, lat)
        sports_biz_pts.append((Point(x, y), b.get("CompanyName2") or b.get("CompanyName1"), b.get("SportType1")))

    commercial_zoning = []
    for shp in ["主計圖-面.shp", "細計-面.shp"]:
        d = load_shapefile_as_geojson(os.path.join(RAW_DIR, "shp", shp))
        for f in d["features"]:
            cat = f["properties"].get("使用分區")
            if cat in {"商業區", "市場用地"} or (cat and "商業區" in cat):
                g = shape(f["geometry"])
                if not g.is_valid:
                    g = g.buffer(0)
                commercial_zoning.append((g, cat))

    park_records = []
    for f in parks_geo["features"]:
        name = f["properties"].get("pm_name")
        lon, lat = f["geometry"]["coordinates"]
        x, y = wgs84_to_proj(lon, lat)
        pt = Point(x, y)
        buf = pt.buffer(RADIUS_M)

        nearby_stations = [n for g, n in station_geoms if buf.intersects(g)]
        nearby_parking_spaces = sum(spaces for g, spaces in parking_pts if buf.contains(g))
        nearby_parking_lots = sum(1 for g, spaces in parking_pts if buf.contains(g))

        market_area = sum(g.intersection(buf).area for g, cat in commercial_zoning if cat == "市場用地")
        commercial_area = sum(
            g.intersection(buf).area for g, cat in commercial_zoning if cat != "市場用地"
        )

        nearby_sports_biz = [(nm, tp) for g, nm, tp in sports_biz_pts if buf.contains(g)]

        info = park_info_by_name.get(name, {})
        tags = tag_facility_types(info)

        park_records.append(
            {
                "name": name,
                "type": info.get("type"),
                "facility_tags": tags,
                "area_m2": info.get("area_m2"),
                "nearby_400m": {
                    "mrt_stations": nearby_stations,
                    "mrt_station_count": len(nearby_stations),
                    "parking_lots": nearby_parking_lots,
                    "parking_spaces": nearby_parking_spaces,
                    "market_zoning_area_m2": round(market_area, 1),
                    "commercial_zoning_area_m2": round(commercial_area, 1),
                    "sports_business_count": len(nearby_sports_biz),
                    "sports_businesses": [{"name": nm, "type": tp} for nm, tp in nearby_sports_biz],
                },
            }
        )

    # 依設施類型分組,看周邊平均值有沒有差異
    from collections import defaultdict

    by_tag = defaultdict(list)
    for r in park_records:
        for t in r["facility_tags"]:
            by_tag[t].append(r)

    tag_summary = {}
    for tag, recs in by_tag.items():
        n = len(recs)
        tag_summary[tag] = {
            "park_count": n,
            "avg_mrt_stations_within_400m": round(sum(r["nearby_400m"]["mrt_station_count"] for r in recs) / n, 2),
            "avg_market_zoning_area_m2": round(
                sum(r["nearby_400m"]["market_zoning_area_m2"] for r in recs) / n, 1
            ),
            "avg_commercial_zoning_area_m2": round(
                sum(r["nearby_400m"]["commercial_zoning_area_m2"] for r in recs) / n, 1
            ),
            "avg_parking_spaces_within_400m": round(
                sum(r["nearby_400m"]["parking_spaces"] for r in recs) / n, 1
            ),
            "pct_with_mrt_within_400m": round(
                100 * sum(1 for r in recs if r["nearby_400m"]["mrt_station_count"] > 0) / n, 1
            ),
            "avg_sports_businesses_within_400m": round(
                sum(r["nearby_400m"]["sports_business_count"] for r in recs) / n, 2
            ),
            "pct_with_sports_business_within_400m": round(
                100 * sum(1 for r in recs if r["nearby_400m"]["sports_business_count"] > 0) / n, 1
            ),
        }

    from clip_utils import site_boundary_3826

    boundary = site_boundary_3826()
    sports_biz_type_counter = Counter()
    total_sports_biz_in_site = 0
    for g, nm, tp in sports_biz_pts:
        if boundary.contains(g):
            total_sports_biz_in_site += 1
            sports_biz_type_counter[tp] += 1

    result = {
        "CAVEAT": (
            "一般商店還是沒有實際 POI 資料,market_zoning_area/commercial_zoning_area 是"
            "都市計畫商業區/市場用地分區面積的代理指標,不是店家清單。運動/健身類商家"
            "現在有真實 POI(sports_business_count/sports_businesses,585筆全市體育署"
            "運動產業登記資料),是實際店名+地址+座標,不是代理指標。人潮來源用捷運站"
            "(含④的進出站人次)+停車場代理,沒有行人量測資料。"
        ),
        "radius_m": RADIUS_M,
        "parks_analyzed": len(park_records),
        "sports_businesses_in_site_total": total_sports_biz_in_site,
        "sports_businesses_citywide_total": len(sports_biz_pts),
        "sports_business_type_distribution_in_site": dict(sports_biz_type_counter.most_common()),
        "summary_by_facility_type": tag_summary,
        "park_details": sorted(
            park_records, key=lambda r: -r["nearby_400m"]["commercial_zoning_area_m2"]
        ),
    }
    with open(os.path.join(PROCESSED_DIR, "analysis7_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("sports businesses in site:", total_sports_biz_in_site, "/ citywide", len(sports_biz_pts))
    print("type distribution:", result["sports_business_type_distribution_in_site"])
    print()
    print(json.dumps(tag_summary, ensure_ascii=False, indent=2))
    print("\ntop 5 parks by nearby sports business count:")
    for r in sorted(park_records, key=lambda r: -r["nearby_400m"]["sports_business_count"])[:5]:
        print(r["name"], r["facility_tags"], r["nearby_400m"]["sports_business_count"], r["nearby_400m"]["sports_businesses"])


if __name__ == "__main__":
    main()
