"""① 周圍綠帶「體量」分析 — 基地 2 公里範圍內的綠地面積與行道樹統計。

真話先講在前面:「體量」原意通常指三維量體(樹冠體積/覆蓋厚度),但現有資料只有
- 樹木普查:座標 + 樹種 + 胸徑(Diameter,樹幹粗細)+ 樹高(TreeHeight)
- 各類綠地/公園/綠帶多邊形:只有 2D 面積

胸徑不等於樹冠寬度,不能拿來推算樹冠覆蓋面積或體積,所以這裡**不生產任何「體積」
數字**,只做:
1. 綠地面積加總(依資料集分類)
2. 行道樹統計(株數、樹高分布、樹種組成)——可以看出綠帶的「量體感」大致落在哪個
   高度區間,但不是真正的體積計算。

若之後要做真正的樹冠體積分析,需要另外補「樹冠寬度/覆蓋半徑」欄位的資料。
"""

import csv
import json
import os

from clip_utils import clip_features_3826, clip_points_xy
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_geojson, load_shapefile_as_geojson


ZONING_GREEN_CATEGORIES = {"公園用地", "綠地用地", "河川區", "保護區"}


def load_zoning_green(shp_name):
    d = load_shapefile_as_geojson(os.path.join(RAW_DIR, "shp", shp_name))
    return [f for f in d["features"] if f["properties"].get("使用分區") in ZONING_GREEN_CATEGORIES]


def load_greenland_layers():
    layers = {
        "公園綠地(J0301)": "parks_greenbelt_J0301.geojson",
        "道路緣帶(J02015)": "road_greenland_J02015.geojson",
        "景觀工程(J05015)": "landscape_projects_J05015.geojson",
        "綠地使用分區(L01015)": "green_zoning_L01015.geojson",
        "公園用地分區(L02015)": "park_zoning_L02015.geojson",
    }
    out = {}
    for label, fname in layers.items():
        d = load_geojson(os.path.join(RAW_DIR, fname))
        out[label] = d["features"]
    return out


def load_street_trees():
    path = os.path.join(RAW_DIR, "street_trees.csv")
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    for r in rows:
        r["TWD97X"] = float(r["TWD97X"]) if r["TWD97X"] else None
        r["TWD97Y"] = float(r["TWD97Y"]) if r["TWD97Y"] else None
        try:
            r["TreeHeight"] = float(r["TreeHeight"])
        except (TypeError, ValueError):
            r["TreeHeight"] = None
        try:
            r["Diameter"] = float(r["Diameter"])
        except (TypeError, ValueError):
            r["Diameter"] = None
    return rows


def area_from_geojson_props(feat):
    v = feat.get("properties", {}).get("面積")
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    greenland = load_greenland_layers()
    area_summary = {}
    clipped_layers = {}
    for label, feats in greenland.items():
        clipped = clip_features_3826(feats)
        clipped_layers[label] = clipped
        total_area_m2 = sum(area_from_geojson_props(f) for f in clipped)
        area_summary[label] = {
            "features_in_site": len(clipped),
            "features_total": len(feats),
            "total_area_m2": round(total_area_m2, 1),
            "total_area_ha": round(total_area_m2 / 10000, 2),
        }
        out_path = os.path.join(
            PROCESSED_DIR, f"green_{label.split('(')[-1].rstrip(')')}_clipped.geojson"
        )
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": clipped}, f, ensure_ascii=False)

    # 都市計畫土地使用分區(主計圖/細計圖)裡的公園用地/綠地用地/河川區/保護區——
    # 這是最權威的官方分區依據,單一來源內部不重疊,適合當作「綠地總量」的主要參考值。
    from shapely.geometry import shape as _shape

    zoning_summary = {}
    for label, shp in [("主計畫", "主計圖-面.shp"), ("細部計畫", "細計-面.shp")]:
        feats = load_zoning_green(shp)
        clipped = clip_features_3826(feats)
        by_cat = {}
        for f in clipped:
            cat = f["properties"]["使用分區"]
            area_m2 = _shape(f["geometry"]).area
            by_cat.setdefault(cat, {"features": 0, "area_m2": 0.0})
            by_cat[cat]["features"] += 1
            by_cat[cat]["area_m2"] += area_m2
        for cat in by_cat:
            by_cat[cat]["area_m2"] = round(by_cat[cat]["area_m2"], 1)
            by_cat[cat]["area_ha"] = round(by_cat[cat]["area_m2"] / 10000, 2)
        zoning_summary[label] = by_cat
        out_path = os.path.join(PROCESSED_DIR, f"green_zoning_{label}_clipped.geojson")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": clipped}, f, ensure_ascii=False)

    trees = load_street_trees()
    trees_in_site = clip_points_xy(trees, "TWD97X", "TWD97Y")

    heights = [t["TreeHeight"] for t in trees_in_site if t["TreeHeight"] is not None]
    species_count = {}
    for t in trees_in_site:
        species_count[t["TreeType"]] = species_count.get(t["TreeType"], 0) + 1
    top_species = sorted(species_count.items(), key=lambda kv: -kv[1])[:15]

    height_bins = {"<5m": 0, "5-10m": 0, "10-15m": 0, "15-20m": 0, ">=20m": 0}
    for h in heights:
        if h < 5:
            height_bins["<5m"] += 1
        elif h < 10:
            height_bins["5-10m"] += 1
        elif h < 15:
            height_bins["10-15m"] += 1
        elif h < 20:
            height_bins["15-20m"] += 1
        else:
            height_bins[">=20m"] += 1

    tree_summary = {
        "trees_in_site": len(trees_in_site),
        "trees_total_citywide": len(trees),
        "avg_height_m": round(sum(heights) / len(heights), 2) if heights else None,
        "avg_diameter_cm": round(
            sum(t["Diameter"] for t in trees_in_site if t["Diameter"] is not None)
            / max(1, len([t for t in trees_in_site if t["Diameter"] is not None])),
            2,
        )
        if trees_in_site
        else None,
        "height_distribution": height_bins,
        "top_species": top_species,
        "NOTE": "無樹冠寬度資料,無法計算樹冠覆蓋面積或體積,以上僅為株數與樹高統計",
    }

    with open(os.path.join(PROCESSED_DIR, "street_trees_clipped.geojson"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [t["TWD97X"], t["TWD97Y"]]},
                        "properties": {
                            "TreeID": t["TreeID"],
                            "TreeType": t["TreeType"],
                            "Diameter": t["Diameter"],
                            "TreeHeight": t["TreeHeight"],
                            "Region": t["Region"],
                            "Dist": t["Dist"],
                        },
                    }
                    for t in trees_in_site
                ],
            },
            f,
            ensure_ascii=False,
        )

    result = {
        "CAVEAT": (
            "greenland_area_by_layer 的 5 個圖層(J0301/J02015/J05015/L01015/L02015)"
            "來自都市設計審議的不同管制圖層,彼此範圍會重疊(例如同一座公園可能同時"
            "出現在公園綠地圖層和綠地使用分區圖層),不能直接加總當作「總綠地面積」。"
            "zoning_green_area_by_source 是都市計畫主計圖/細部計畫的公園用地/綠地用地/"
            "河川區/保護區分區面積,單一來源內部不重疊,較適合當作綠地總量的主要參考,"
            "但主計畫跟細部計畫兩者之間本身也會有重疊(細部計畫是主計畫的加細版)。"
        ),
        "greenland_area_by_layer": area_summary,
        "zoning_green_area_by_source": zoning_summary,
        "street_trees": tree_summary,
    }
    with open(os.path.join(PROCESSED_DIR, "analysis1_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
