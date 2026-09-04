"""② 找出周邊代表基地特色的街區 — 用都市計畫土地使用分區 + 近年建照分布來描述街廓特色。

真話先講在前面:目前**完全沒有建物 footprint(建築物外形)或地籍資料**,所以這裡
做不到「街廓」層級的容積率/建物量體/屋齡等直接統計,只能做:
1. 主計畫/細部計畫土地使用分區在基地內的組成(住宅區/商業區/文教區…佔比)
2. 街廓編號(街廓編號欄位在資料裡幾乎是空的,只有極少數,見輸出裡的 note)
3. 近年建照(建築執照)點位分布,做為「哪裡有新建/改建活動」的間接指標

這些只能反映「土地使用分區」跟「近年開發動態」這兩個側面,不是真正的建成環境
街廓特色分析。要做到那個程度,需要建物 footprint、樓層數、屋齡、地籍等資料——
使用者已表示待會補建物資料。
"""

import json
import os

from clip_utils import clip_features_3826
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_geojson, load_shapefile_as_geojson


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    from shapely.geometry import shape as _shape

    zoning_mix = {}
    block_id_coverage = {}
    for label, shp in [("主計畫", "主計圖-面.shp"), ("細部計畫", "細計-面.shp")]:
        d = load_shapefile_as_geojson(os.path.join(RAW_DIR, "shp", shp))
        clipped = clip_features_3826(d["features"])
        by_cat = {}
        with_block_id = 0
        skipped_boundary_lines = 0
        for f in clipped:
            cat = f["properties"].get("使用分區")
            if not cat:
                # 分區代碼「細部計畫範圍」這類是計畫邊界線/範圍框,不是實際土地使用
                # 分區,且其中部分幾何在原始 shapefile 是純內環(hole-only)的無效多邊形
                # (讀取時 pyshp 有警告),算出的面積會是離譜的天文數字,必須排除。
                skipped_boundary_lines += 1
                continue
            area_m2 = _shape(f["geometry"]).area
            by_cat.setdefault(cat, {"features": 0, "area_m2": 0.0})
            by_cat[cat]["features"] += 1
            by_cat[cat]["area_m2"] += area_m2
            if f["properties"].get("街廓編號"):
                with_block_id += 1
        for cat in by_cat:
            by_cat[cat]["area_m2"] = round(by_cat[cat]["area_m2"], 1)
            by_cat[cat]["area_ha"] = round(by_cat[cat]["area_m2"] / 10000, 2)
        total_area = sum(v["area_m2"] for v in by_cat.values())
        for cat in by_cat:
            by_cat[cat]["pct_of_site_zoning_area"] = (
                round(100 * by_cat[cat]["area_m2"] / total_area, 1) if total_area else None
            )
        zoning_mix[label] = dict(sorted(by_cat.items(), key=lambda kv: -kv[1]["area_m2"]))
        block_id_coverage[label] = {
            "features_in_site": len(clipped),
            "features_with_街廓編號": with_block_id,
            "skipped_boundary_line_features": skipped_boundary_lines,
        }
        out_path = os.path.join(PROCESSED_DIR, f"zoning_{label}_clipped.geojson")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": clipped}, f, ensure_ascii=False)

    permits = load_geojson(os.path.join(RAW_DIR, "building_permits_H05011.geojson"))
    permits_clipped = clip_features_3826(permits["features"])
    year_count = {}
    for f in permits_clipped:
        name = f["properties"].get("名稱", "")
        # 名稱格式如「104建0258」→ 民國年 104
        year = name[:3] if name[:3].isdigit() else "未知"
        year_count[year] = year_count.get(year, 0) + 1
    with open(os.path.join(PROCESSED_DIR, "building_permits_clipped.geojson"), "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": permits_clipped}, f, ensure_ascii=False)

    result = {
        "CAVEAT": "無建物 footprint/地籍資料,以下僅為土地使用分區組成與建照點位分布,不是完整的街廓特色分析",
        "zoning_mix_by_source": zoning_mix,
        "block_id_field_coverage": block_id_coverage,
        "building_permits": {
            "permits_in_site": len(permits_clipped),
            "permits_total_citywide": len(permits["features"]),
            "by_roc_year": dict(sorted(year_count.items())),
        },
    }
    with open(os.path.join(PROCESSED_DIR, "analysis2_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
