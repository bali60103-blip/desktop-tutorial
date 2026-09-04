"""⑧ Overpass OSM POI(餐飲/公園/辦公室/零售等)彙整。

使用者陸續用 overpass-turbo 分批查詢不同類別(目前收到:超商 shop=convenience、
咖啡廳 amenity=cafe),每批存成 data/raw/osm_poi_*.json(Overpass 原生 JSON,不是
GeoJSON——node 型態,geometry 用 lat/lon,不是 GeoJSON 的 [lon,lat]),這支腳本會
自動抓所有符合這個檔名規則的檔案、合併、依 tags 分類、裁切到基地範圍。

分類邏輯(用 OSM tag 判斷,不是憑店名猜):
- 餐飲:amenity in {restaurant, cafe, fast_food, bar, pub, food_court, ice_cream}
- 公園/綠地:leisure in {park, garden}
- 辦公室:office 有值,或 building=office
- 零售/商店:shop 有值(含超商,shop=convenience)

同一個 OSM node 可能同時有 amenity 跟 shop 兩個 tag(例如飲料店常常
amenity=cafe + shop=beverages),分類到「餐飲」也分類到「零售」,不互斥,
跟先前公園設施分類的處理方式一致。

**這是目前基地內最接近「真正商店清單」的資料**,比之前用都市計畫商業區/市場
用地面積當代理指標準確得多——但 OSM 是志工協作地圖,不保證涵蓋率100%,實際
店家數量可能比這裡列出的更多(尤其辦公室,OSM 上普遍標記不齊全,已經在對話裡
提醒過)。
"""

import glob
import json
import os

from shapely.geometry import Point

from clip_utils import site_boundary_3826
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_geojson, wgs84_to_proj

DINING_AMENITY = {"restaurant", "cafe", "fast_food", "bar", "pub", "food_court", "ice_cream"}
PARK_LEISURE = {"park", "garden"}


def classify(tags):
    cats = []
    if tags.get("amenity") in DINING_AMENITY:
        cats.append("餐飲")
    if tags.get("leisure") in PARK_LEISURE:
        cats.append("公園綠地")
    if tags.get("office") or tags.get("building") == "office":
        cats.append("辦公室")
    if tags.get("shop"):
        cats.append("零售/商店")
    return cats or ["未分類"]


def _clean(s):
    """部分 RTF 貼上的資料裡混了破損的 UTF-16 代理對(通常是 emoji 之類的擴充字元
    被 striprtf 轉壞了),寫回 JSON 時會讓 utf-8 編碼直接炸掉,這裡把無法編碼的
    字元換成替代符號,不讓一筆壞資料搞垮整批。"""
    if not isinstance(s, str):
        return s
    return s.encode("utf-8", errors="replace").decode("utf-8")


def element_center(el):
    """node 直接有 lat/lon;way/relation 若查詢時用了 `out center`,會有 center.lat/lon。"""
    if "lat" in el and "lon" in el:
        return el["lat"], el["lon"]
    if "center" in el:
        return el["center"]["lat"], el["center"]["lon"]
    return None


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(RAW_DIR, "osm_poi_*.json")))
    if not files:
        print("no osm_poi_*.json files found in data/raw/, skipping")
        return

    boundary = site_boundary_3826()
    seen_ids = set()
    all_pois = []
    for path in files:
        d = load_geojson(path)
        for el in d.get("elements", []):
            osm_id = (el.get("type"), el.get("id"))
            if osm_id in seen_ids:
                continue
            seen_ids.add(osm_id)
            center = element_center(el)
            if not center:
                continue
            lat, lon = center
            x, y = wgs84_to_proj(lon, lat)
            pt = Point(x, y)
            if not boundary.contains(pt):
                continue
            tags = el.get("tags", {})
            if not tags:
                # 查詢用了遞迴抓 way 的成員節點(例如 `(._;>;);`)時,常常會混進大量
                # 沒有任何 tag、只是建築物多邊形頂點的裸節點,不是真正的 POI,直接跳過
                # 不列入統計,避免灌水或誤標成「未分類」讓人以為是不明店家。
                continue
            all_pois.append(
                {
                    "osm_type": el.get("type"),
                    "osm_id": el.get("id"),
                    "name": _clean(tags.get("name") or tags.get("brand") or "(無名稱)"),
                    "categories": classify(tags),
                    "amenity": tags.get("amenity"),
                    "shop": tags.get("shop"),
                    "leisure": tags.get("leisure"),
                    "office": tags.get("office"),
                    "address": _clean(tags.get("addr:full")),
                    "opening_hours": tags.get("opening_hours"),
                    "lon": lon,
                    "lat": lat,
                }
            )

    from collections import Counter

    cat_counter = Counter()
    for p in all_pois:
        for c in p["categories"]:
            cat_counter[c] += 1

    amenity_counter = Counter(p["amenity"] for p in all_pois if p["amenity"])
    shop_counter = Counter(p["shop"] for p in all_pois if p["shop"])

    with open(os.path.join(PROCESSED_DIR, "osm_poi_clipped.geojson"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
                        "properties": {k: v for k, v in p.items() if k not in ("lon", "lat")},
                    }
                    for p in all_pois
                ],
            },
            f,
            ensure_ascii=False,
        )

    result = {
        "CAVEAT": (
            "OSM 是志工協作地圖,不保證100%涵蓋——尤其辦公室(office tag)在OSM上"
            "普遍標記不齊全,這裡的辦公室數字很可能是低估。這是目前手上最接近「真正"
            "商店清單」的資料,比都市計畫商業區/市場用地面積代理指標準確,但不是"
            "官方統計,無法保證完整性。"
        ),
        "source_files": [os.path.basename(f) for f in files],
        "total_pois_in_site": len(all_pois),
        "category_counts": dict(cat_counter.most_common()),
        "amenity_type_counts": dict(amenity_counter.most_common()),
        "shop_type_counts": dict(shop_counter.most_common(20)),
    }
    with open(os.path.join(PROCESSED_DIR, "analysis8_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"source files: {result['source_files']}")
    print(f"total POIs in site: {len(all_pois)}")
    print("category_counts:", result["category_counts"])
    print("amenity_type_counts:", result["amenity_type_counts"])


if __name__ == "__main__":
    main()
