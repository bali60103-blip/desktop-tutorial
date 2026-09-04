"""建物 footprint/樓高的細部統計:各分區類別的樓高/密度、200m 網格量體密度面。

前提:只用「已收到建物網格」涵蓋到的範圍(見 analysis2 的 building_footprints.
coverage_note),涵蓋率目前約 94.7%(2026-09-04)。網格/分區統計都只計算落在有
建物資料範圍內的部分,不會把「沒資料」誤算成「這裡沒建物」。

輸出:
- ../../data/processed/building_stats_by_zoning.json — 依 細部計畫 使用分區 的
  建物棟數/樓高統計/建蔽率(footprint 面積 / 分區面積,僅計算分區落在建物資料
  涵蓋範圍內的部分)
- ../../data/processed/building_density_grid.geojson — 200m 網格,每格建物棟數
  跟平均樓高,可疊圖看基地內量體/密度的空間分布(這是回答②「街區特色」最直接
  的一塊)
"""

import glob
import json
import math
import os

from shapely.geometry import box, shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

from clip_utils import clip_features_3826, site_boundary_3826
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_geojson, wgs84_to_proj

GRID_SIZE_M = 200


def load_buildings_3826_clipped():
    """Returns (clipped_building_geoms_3826_with_props, tile_bbox_union_3826)."""
    building_tiles = sorted(glob.glob(os.path.join(RAW_DIR, "buildings_tile_*.json")))
    all_buildings = []
    tile_boxes = []
    for path in building_tiles:
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
            g3826 = transform(lambda lon, lat: wgs84_to_proj(lon, lat), shape(f["geometry"]))
            all_buildings.append({"geometry": g3826.__geo_interface__, "properties": f["properties"]})
        tile_boxes.append(
            transform(lambda lon, lat: wgs84_to_proj(lon, lat), box(min(lons), min(lats), max(lons), max(lats)))
        )

    clipped = clip_features_3826(all_buildings)
    coverage_union = unary_union(tile_boxes) if tile_boxes else None
    return clipped, coverage_union


def stats_by_zoning(buildings_clipped, coverage_union):
    with open(os.path.join(PROCESSED_DIR, "zoning_細部計畫_clipped.geojson"), encoding="utf-8") as f:
        zoning = json.load(f)["features"]

    zone_geoms = []
    zone_props = []
    for f in zoning:
        cat = f["properties"].get("使用分區")
        if not cat:
            continue
        g = shape(f["geometry"])
        if not g.is_valid:
            # 部分 shapefile 多邊形因環方向問題(見 analysis2 的說明)讀出來是無效
            # 幾何,buffer(0) 是標準修復手法,重建有效的多邊形。
            g = g.buffer(0)
        zone_geoms.append(g)
        zone_props.append(cat)

    tree = STRtree(zone_geoms)
    by_cat = {}
    building_centroids = [(shape(f["geometry"]), f["properties"].get("height")) for f in buildings_clipped]

    for geom, height in building_centroids:
        c = geom.centroid
        idxs = tree.query(c)
        cat = None
        for i in idxs:
            if zone_geoms[i].contains(c):
                cat = zone_props[i]
                break
        if cat is None:
            cat = "(不在任何分區內/計畫範圍外)"
        d = by_cat.setdefault(cat, {"building_count": 0, "footprint_area_m2": 0.0, "heights": []})
        d["building_count"] += 1
        d["footprint_area_m2"] += geom.area
        if height is not None:
            d["heights"].append(height)

    # 分區面積(僅計算落在建物資料涵蓋範圍內的部分,避免建蔽率被沒資料的角落拉低)
    zone_area_covered = {}
    for geom, cat in zip(zone_geoms, zone_props):
        covered = geom.intersection(coverage_union).area if coverage_union else 0.0
        zone_area_covered[cat] = zone_area_covered.get(cat, 0.0) + covered

    result = {}
    for cat, d in sorted(by_cat.items(), key=lambda kv: -kv[1]["building_count"]):
        heights = d["heights"]
        area_covered = zone_area_covered.get(cat, 0.0)
        result[cat] = {
            "building_count": d["building_count"],
            "avg_height_m": round(sum(heights) / len(heights), 2) if heights else None,
            "median_height_m": round(sorted(heights)[len(heights) // 2], 2) if heights else None,
            "max_height_m": round(max(heights), 2) if heights else None,
            "total_footprint_area_m2": round(d["footprint_area_m2"], 1),
            "zone_area_within_building_coverage_m2": round(area_covered, 1),
            "footprint_coverage_ratio": (
                round(d["footprint_area_m2"] / area_covered, 3) if area_covered > 100 else None
            ),
        }
    return result


def density_grid(buildings_clipped):
    boundary = site_boundary_3826()
    minx, miny, maxx, maxy = boundary.bounds
    nx = math.ceil((maxx - minx) / GRID_SIZE_M)
    ny = math.ceil((maxy - miny) / GRID_SIZE_M)

    cells = []
    cell_geoms = []
    for i in range(nx):
        for j in range(ny):
            cx0, cy0 = minx + i * GRID_SIZE_M, miny + j * GRID_SIZE_M
            cell = box(cx0, cy0, cx0 + GRID_SIZE_M, cy0 + GRID_SIZE_M)
            if boundary.intersects(cell):
                cells.append(cell.intersection(boundary))
                cell_geoms.append(cell)

    tree = STRtree(cell_geoms)
    counts = [0] * len(cell_geoms)
    height_sums = [0.0] * len(cell_geoms)
    height_counts = [0] * len(cell_geoms)
    footprint_sums = [0.0] * len(cell_geoms)

    for f in buildings_clipped:
        geom = shape(f["geometry"])
        c = geom.centroid
        idxs = tree.query(c)
        for i in idxs:
            if cell_geoms[i].contains(c):
                counts[i] += 1
                footprint_sums[i] += geom.area
                h = f["properties"].get("height")
                if h is not None:
                    height_sums[i] += h
                    height_counts[i] += 1
                break

    from gis_utils import proj_to_wgs84

    features = []
    for i, cell in enumerate(cells):
        if counts[i] == 0:
            continue
        cell_wgs84 = transform(lambda x, y: proj_to_wgs84(x, y), cell)
        features.append(
            {
                "type": "Feature",
                "geometry": cell_wgs84.__geo_interface__,
                "properties": {
                    "building_count": counts[i],
                    "avg_height_m": round(height_sums[i] / height_counts[i], 2) if height_counts[i] else None,
                    "footprint_coverage_ratio": round(footprint_sums[i] / cell_geoms[i].area, 3),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def main():
    buildings_clipped, coverage_union = load_buildings_3826_clipped()
    if not buildings_clipped:
        print("no building tiles found, skipping building_stats")
        return

    by_zoning = stats_by_zoning(buildings_clipped, coverage_union)
    with open(os.path.join(PROCESSED_DIR, "building_stats_by_zoning.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "CAVEAT": (
                    "building_count/footprint 只統計落在目前已收到建物網格範圍內的分區部分。"
                    "footprint_coverage_ratio(建物 footprint 面積/分區在建物資料涵蓋範圍內的面積)"
                    "是建蔽率的粗略代理,不是正式建蔽率(正式建蔽率該用地籍上的建築線退縮規範"
                    "去算,這裡只是簡單面積比)。分區面積小於 100 平方公尺的不計算比例(避免"
                    "極端值)。"
                ),
                "by_zoning_category": by_zoning,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    grid = density_grid(buildings_clipped)
    with open(os.path.join(PROCESSED_DIR, "building_density_grid.geojson"), "w", encoding="utf-8") as f:
        json.dump(grid, f, ensure_ascii=False)

    print(f"zoning categories: {len(by_zoning)}")
    print(f"density grid cells with buildings: {len(grid['features'])}")
    top5 = list(by_zoning.items())[:5]
    for cat, s in top5:
        print(cat, s)


if __name__ == "__main__":
    main()
