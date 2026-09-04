"""② 找出周邊代表基地特色的街區 — 土地使用分區 + 建照 + (部分)建物 footprint/樓高。

真話先講在前面:
- 都市計畫分區(住宅區/商業區/文教區…佔比)跟建照點位分布,只能反映分區跟近年
  開發動態,不是真正的建成環境街廓特色。
- 建物 footprint + 樓高資料**目前只有部分涵蓋**:使用者是用「臺北市建物3D模型」
  按網格分批提供,已收到的網格只覆蓋基地北側一小塊(大同/中山區靠雙連站一帶),
  基地主體(市民大道走廊本身、台北車站、華山一帶)還沒有建物資料,見輸出裡的
  `building_footprints.coverage_note`,千萬不要把這個部分結果當成完整基地的建物
  統計。之後使用者補齊其他網格後,重跑這支腳本就會自動合併(見 glob 那段)。
"""

import glob
import json
import os

from clip_utils import clip_features_3826, site_boundary_3826
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

    # -- 建物 footprint + 樓高(部分網格,見檔頭說明) --
    from shapely.geometry import shape as _shape2
    from shapely.ops import transform as _transform
    from gis_utils import wgs84_to_proj as _to_proj

    building_tiles = sorted(glob.glob(os.path.join(RAW_DIR, "buildings_tile_*.json")))
    all_buildings = []
    tile_names = []
    for path in building_tiles:
        tile_names.append(os.path.basename(path))
        d = load_geojson(path)
        all_buildings.extend(d["features"])

    buildings_summary = None
    if all_buildings:
        buildings_3826 = []
        tile_bboxes_3826 = {}
        for path in building_tiles:
            name = os.path.basename(path)
            feats = load_geojson(path)["features"]
            lons, lats = [], []

            def _rec(c, lons=lons, lats=lats):
                if isinstance(c[0], (int, float)):
                    lons.append(c[0])
                    lats.append(c[1])
                else:
                    for cc in c:
                        _rec(cc)

            for f in feats:
                _rec(f["geometry"]["coordinates"])
                g3826 = _transform(lambda lon, lat: _to_proj(lon, lat), _shape2(f["geometry"]))
                buildings_3826.append({"geometry": g3826.__geo_interface__, "properties": f["properties"]})
            from shapely.geometry import box as _box

            tile_bboxes_3826[name] = _transform(
                lambda lon, lat: _to_proj(lon, lat), _box(min(lons), min(lats), max(lons), max(lats))
            )

        buildings_clipped = clip_features_3826(buildings_3826)
        heights = [f["properties"].get("height") for f in buildings_clipped if f["properties"].get("height") is not None]
        with open(os.path.join(PROCESSED_DIR, "buildings_clipped.geojson"), "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": buildings_clipped}, f, ensure_ascii=False)

        from shapely.ops import unary_union

        boundary = site_boundary_3826()
        site_area = boundary.area
        coverage_by_tile_pct = {
            name: round(boundary.intersection(bbox).area / site_area * 100, 1)
            for name, bbox in tile_bboxes_3826.items()
        }
        combined_bbox_coverage_pct = round(
            unary_union(list(tile_bboxes_3826.values())).intersection(boundary).area / site_area * 100, 1
        )
        buildings_summary = {
            "source_tiles_received": tile_names,
            "coverage_note": (
                "buildings_in_site_boundary 是目前已收到網格範圍內的實際建物數,不是整個基地的"
                "建物總數。approx_site_area_covered_pct 是用各網格的外框(bounding box,不是"
                "實際建物分布形狀)估的粗略涵蓋率,可能比實際涵蓋率略高(外框內不一定每個角落"
                "都真的畫到建物)。缺口在哪裡看 tile 座標範圍自己判斷,還沒有自動標示。"
            ),
            "approx_site_area_covered_pct_by_tile": coverage_by_tile_pct,
            "approx_site_area_covered_pct_combined": combined_bbox_coverage_pct,
            "buildings_total_in_received_tiles": len(all_buildings),
            "buildings_in_site_boundary": len(buildings_clipped),
            "avg_height_m": round(sum(heights) / len(heights), 2) if heights else None,
            "max_height_m": round(max(heights), 2) if heights else None,
        }

    result = {
        "CAVEAT": "土地使用分區組成+建照點位是全基地涵蓋;建物 footprint/樓高目前只有部分網格,見 building_footprints",
        "zoning_mix_by_source": zoning_mix,
        "block_id_field_coverage": block_id_coverage,
        "building_permits": {
            "permits_in_site": len(permits_clipped),
            "permits_total_citywide": len(permits["features"]),
            "by_roc_year": dict(sorted(year_count.items())),
        },
        "building_footprints": buildings_summary
        or {"status": "尚未收到任何建物 footprint 資料"},
    }
    with open(os.path.join(PROCESSED_DIR, "analysis2_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
