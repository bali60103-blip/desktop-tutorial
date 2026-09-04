"""⑤ 綠帶對城市滲透性的幫助 —— 依 Jane Jacobs / Jan Gehl / Richard Sennett 的論點拆解成
可測量指標。方法論見 README「⑤ 滲透性分析」那節,這裡只放程式跟必要註解。

五個子分析,依可信度排序(前三個資料紮實,後兩個是代理指標,要謹慎解讀):
1. edge_porosity      — Sennett「boundary vs border」:綠地邊界上的步行設施接觸密度
2. walk_catchment      — Gehl 400m/800m 步行可及性圈
3. edge_building_density — Gehl edge effect:綠地邊界緊鄰建物密度(活躍邊界代理)
4. block_grain         — Jacobs 街廓尺度/路徑選擇(用道路線段密度代理,無正式路網 graph)
5. green_fragmentation — Jacobs 綠地連通:各綠地斑塊間最近距離、是否有步行設施相連

全部只計算落在「基地 2km 緩衝範圍」內的部分;②③依賴建物資料,只涵蓋目前收到的
約 94.7% 建物網格,不是全基地。
"""

import json
import os

from shapely.geometry import shape, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

from clip_utils import clip_features_3826, site_boundary_3826
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_geojson, load_shapefile_as_geojson

MIN_PATCH_AREA_M2 = 500  # 濾掉太小的碎片(交通島之類),避免統計被雜訊淹沒
EDGE_ZONE_M = 30  # Gehl edge effect 的「邊界帶」寬度
WALK_RINGS_M = [400, 800]


def load_green_patches():
    """公園用地+綠地用地+保護區,合併相鄰/重疊的碎片成獨立「綠地斑塊」。
    河川區(水域本身)不算在「可步行滲透的綠地」裡,另外處理。"""
    d = load_shapefile_as_geojson(os.path.join(RAW_DIR, "shp", "細計-面.shp"))
    feats = [f for f in d["features"] if f["properties"].get("使用分區") in {"公園用地", "綠地用地", "保護區"}]
    clipped = clip_features_3826(feats)
    geoms = []
    for f in clipped:
        g = shape(f["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        geoms.append(g)
    merged = unary_union([g.buffer(0.5) for g in geoms]).buffer(-0.5)
    patches = [merged] if merged.geom_type == "Polygon" else list(merged.geoms)
    patches = [p for p in patches if p.area >= MIN_PATCH_AREA_M2]
    return patches


def load_pedestrian_points():
    """人行道/坡道/天橋/地下道的「接觸點」集合,當作 Sennett 講的邊界開口代理。"""
    pts = []

    ramps = load_geojson(os.path.join(RAW_DIR, "accessibility_ramps.json"))
    for f in ramps["features"]:
        x, y = f["geometry"]["coordinates"]
        pts.append(Point(x, y))

    from gis_utils import wgs84_to_proj

    for name, key_lon, key_lat in [
        ("footbridges.json", "Obj_Longitude", "Obj_Latitude"),
        ("underpasses.json", "Obj_Longitude", "Obj_Latitude"),
    ]:
        d = load_geojson(os.path.join(RAW_DIR, name))
        for item in d:
            x, y = wgs84_to_proj(item[key_lon], item[key_lat])
            pts.append(Point(x, y))

    return pts


def load_tree_points():
    import csv

    with open(os.path.join(RAW_DIR, "street_trees.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pts = []
    for r in rows:
        try:
            pts.append(Point(float(r["TWD97X"]), float(r["TWD97Y"])))
        except (TypeError, ValueError, KeyError):
            continue
    return pts


def load_sidewalk_lines():
    sw = load_geojson(os.path.join(RAW_DIR, "sidewalks.json"))
    lines = [shape(f["geometry"]) for f in sw["features"]]
    painted = load_shapefile_as_geojson(os.path.join(RAW_DIR, "shp", "grapline_21_15.shp"), encoding="utf-8")
    lines += [shape(f["geometry"]) for f in painted["features"]]
    return lines


def edge_porosity(patches, ped_points, sidewalk_lines):
    """Sennett:每 100m 綠地邊界上,有幾個步行設施接觸點(坡道/天橋/地下道落在邊界帶內,
    +人行道跟邊界線相交的次數)。數字越高 = 邊界越像 border(可滲透),越低 = 越像
    boundary(封閉牆面/圍籬效果)。"""
    ped_tree = STRtree(ped_points)
    results = []
    for i, patch in enumerate(patches):
        boundary = patch.exterior
        edge_zone = patch.buffer(8).difference(patch.buffer(-2))  # 邊界內外各幾公尺的窄帶
        idxs = ped_tree.query(edge_zone)
        ramp_like_count = sum(1 for j in idxs if edge_zone.contains(ped_points[j]))

        crossing_count = sum(1 for line in sidewalk_lines if boundary.intersects(line))

        perimeter_m = boundary.length
        openings = ramp_like_count + crossing_count
        porosity_per_100m = round(openings / (perimeter_m / 100), 2) if perimeter_m else None
        results.append(
            {
                "patch_id": i,
                "area_m2": round(patch.area, 1),
                "perimeter_m": round(perimeter_m, 1),
                "ramp_or_crossing_points": openings,
                "porosity_index_per_100m_edge": porosity_per_100m,
                "centroid_3826": [round(patch.centroid.x, 1), round(patch.centroid.y, 1)],
            }
        )
    return results


def walk_catchment(patches, buildings):
    green_union = unary_union(patches)
    building_pts = [(shape(f["geometry"]).centroid, f) for f in buildings]

    def ring_for(pt):
        d = pt.distance(green_union)
        for r in WALK_RINGS_M:
            if d <= r:
                return r
        return None

    counts = {r: 0 for r in WALK_RINGS_M}
    counts["outside"] = 0
    for pt, _ in building_pts:
        r = ring_for(pt)
        if r is None:
            counts["outside"] += 1
        else:
            counts[r] += 1
    total = len(building_pts)
    return {
        "total_buildings_evaluated": total,
        "within_400m_count": counts[400],
        "within_400m_pct": round(100 * counts[400] / total, 1) if total else None,
        "within_800m_count": counts[800] + counts[400],
        "within_800m_pct": round(100 * (counts[800] + counts[400]) / total, 1) if total else None,
        "outside_800m_count": counts["outside"],
        "outside_800m_pct": round(100 * counts["outside"] / total, 1) if total else None,
        "NOTE": "算的是「棟數」涵蓋率,不是人口涵蓋率(沒有居住單元/人口資料)",
    }


def edge_building_density(patches, buildings):
    building_geoms = [shape(f["geometry"]) for f in buildings]
    tree = STRtree(building_geoms)
    results = []
    for i, patch in enumerate(patches):
        edge_band = patch.buffer(EDGE_ZONE_M).difference(patch)
        idxs = tree.query(edge_band)
        touching = [building_geoms[j] for j in idxs if edge_band.intersects(building_geoms[j])]
        perimeter_m = patch.exterior.length
        density_per_100m = round(len(touching) / (perimeter_m / 100), 2) if perimeter_m else None
        results.append(
            {
                "patch_id": i,
                "buildings_within_30m_of_edge": len(touching),
                "buildings_per_100m_perimeter": density_per_100m,
                "perimeter_m": round(perimeter_m, 1),
            }
        )
    return results


def block_grain():
    """Jacobs 街廓尺度代理:用 roadsize2(道路寬度分類,22,676 段,較 8mroadup Road.shp
    更完整)算「細街廓/人行尺度道路」佔比——road_width < 8m 的道路通常是巷弄尺度,
    密度越高代表街廓越破碎、路徑選擇越多;>=20m 的是快速道路/主幹道,是切割街廓、
    降低滲透性的一方。仍然沒有正式路網節點/拓樸,是道路寬度分級密度代理,不是
    路口數或最短路徑選擇數的直接量測。"""
    roads = load_shapefile_as_geojson(os.path.join(RAW_DIR, "shp", "roadsize2.shp"), encoding="utf-8")
    clipped = clip_features_3826(roads["features"])

    def parse_width(w):
        try:
            return float(str(w).rstrip("M"))
        except (TypeError, ValueError):
            return None

    fine_len, wide_len, mid_len, total_len = 0.0, 0.0, 0.0, 0.0
    for f in clipped:
        length = shape(f["geometry"]).length
        w = parse_width(f["properties"].get("road_width"))
        total_len += length
        if w is not None and w < 8:
            fine_len += length
        elif w is not None and w >= 20:
            wide_len += length
        else:
            mid_len += length

    boundary = site_boundary_3826()
    area_km2 = boundary.area / 1_000_000
    return {
        "road_segments_in_site": len(clipped),
        "total_road_length_km": round(total_len / 1000, 2),
        "road_density_km_per_km2": round((total_len / 1000) / area_km2, 2),
        "fine_grain_lt8m_length_km": round(fine_len / 1000, 2),
        "fine_grain_lt8m_pct_of_total": round(100 * fine_len / total_len, 1) if total_len else None,
        "mid_8to20m_length_km": round(mid_len / 1000, 2),
        "wide_ge20m_length_km": round(wide_len / 1000, 2),
        "wide_ge20m_pct_of_total": round(100 * wide_len / total_len, 1) if total_len else None,
        "NOTE": "沒有正式路網節點/拓樸資料,這是道路寬度分級密度代理,不是路口密度或路徑選擇數的直接量測",
    }


def green_fragmentation(patches, ped_points, tree_points):
    """Jacobs 綠地連通:各斑塊形心兩兩最近距離,以及斑塊間是否有步行設施/行道樹在
    兩者之間的走廊上(粗略:兩斑塊凸包間 50m 緩衝內是否有步行設施/行道樹點位)。

    多加行道樹是因為:就算兩塊綠地之間有人行道相連(pedestrian_link_detected),
    那條路線走起來是不是「綠意連續」是另一件事——沒有行道樹的話,人行道只是
    灰色基礎設施把兩塊綠地在地圖上連起來,不是 Jacobs/Gehl 講的那種讓人願意
    走、有生活感的綠廊。tree_linked 用「走廊內至少 5 株樹」當門檻,是粗略判斷,
    沒有精確到「連續林蔭」的程度。"""
    centroids = [p.centroid for p in patches]
    n = len(patches)
    ped_tree = STRtree(ped_points)
    tree_str = STRtree(tree_points)
    nearest = []
    for i in range(n):
        dists = [(centroids[i].distance(centroids[j]), j) for j in range(n) if j != i]
        if not dists:
            continue
        dmin, j = min(dists)
        gap = patches[i].distance(patches[j])
        corridor = patches[i].union(patches[j]).convex_hull.buffer(50).difference(patches[i]).difference(patches[j])

        ped_idxs = ped_tree.query(corridor)
        linked = sum(1 for k in ped_idxs if corridor.contains(ped_points[k])) > 0

        tree_idxs = tree_str.query(corridor)
        trees_in_corridor = sum(1 for k in tree_idxs if corridor.contains(tree_points[k]))

        nearest.append(
            {
                "patch_id": i,
                "nearest_patch_id": j,
                "gap_distance_m": round(gap, 1),
                "pedestrian_link_detected": linked,
                "trees_in_corridor": trees_in_corridor,
                "tree_linked": trees_in_corridor >= 5,
            }
        )
    return nearest


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    patches = load_green_patches()
    ped_points = load_pedestrian_points()
    sidewalk_lines = load_sidewalk_lines()
    tree_points = load_tree_points()

    import glob

    building_tiles = sorted(glob.glob(os.path.join(RAW_DIR, "buildings_tile_*.json")))
    buildings_3826 = []
    from shapely.ops import transform
    from gis_utils import wgs84_to_proj

    for path in building_tiles:
        for f in load_geojson(path)["features"]:
            g3826 = transform(lambda lon, lat: wgs84_to_proj(lon, lat), shape(f["geometry"]))
            buildings_3826.append({"geometry": g3826.__geo_interface__, "properties": f["properties"]})
    buildings_clipped = clip_features_3826(buildings_3826)

    porosity = edge_porosity(patches, ped_points, sidewalk_lines)
    catchment = walk_catchment(patches, buildings_clipped)
    edge_density = edge_building_density(patches, buildings_clipped)
    grain = block_grain()
    fragmentation = green_fragmentation(patches, ped_points, tree_points)

    porosity_sorted = sorted(porosity, key=lambda r: -(r["porosity_index_per_100m_edge"] or 0))
    edge_density_sorted = sorted(edge_density, key=lambda r: -(r["buildings_per_100m_perimeter"] or 0))

    n_links = len(fragmentation)
    n_ped_linked = sum(1 for r in fragmentation if r["pedestrian_link_detected"])
    n_tree_linked = sum(1 for r in fragmentation if r["tree_linked"])
    n_ped_but_not_tree = sum(1 for r in fragmentation if r["pedestrian_link_detected"] and not r["tree_linked"])
    fragmentation_summary = {
        "nearest_neighbor_pairs": n_links,
        "pedestrian_linked_pct": round(100 * n_ped_linked / n_links, 1) if n_links else None,
        "tree_linked_pct": round(100 * n_tree_linked / n_links, 1) if n_links else None,
        "pedestrian_linked_but_treeless_pct": round(100 * n_ped_but_not_tree / n_links, 1) if n_links else None,
        "NOTE": (
            "pedestrian_linked_but_treeless = 兩塊綠地之間雖然有人行道相連,但走廊內"
            "行道樹不到5株——連得起來,但不是真的綠廊,是這次新增行道樹分析後最直接"
            "可以拿來論證的落差。"
        ),
    }

    result = {
        "CAVEAT": (
            "green patches = 公園用地+綠地用地+保護區(不含河川區水域本身),"
            f"面積小於 {MIN_PATCH_AREA_M2} 平方公尺的碎片已濾掉。②③依賴建物資料,"
            "只涵蓋目前已收到的建物網格範圍(約94.7%)。④沒有正式路網拓樸,是路段"
            "密度代理。⑤的『步行連結偵測』是簡化的凸包走廊判斷,不是最短路徑分析。"
        ),
        "green_patch_count": len(patches),
        "sennett_edge_porosity_top10_most_porous": porosity_sorted[:10],
        "sennett_edge_porosity_bottom10_least_porous": porosity_sorted[-10:],
        "gehl_walk_catchment": catchment,
        "gehl_edge_building_density_top10": edge_density_sorted[:10],
        "gehl_edge_building_density_bottom10": edge_density_sorted[-10:],
        "jacobs_block_grain": grain,
        "jacobs_green_fragmentation": fragmentation,
        "jacobs_green_fragmentation_summary": fragmentation_summary,
    }
    with open(os.path.join(PROCESSED_DIR, "analysis5_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 完整逐斑塊資料另存,供出圖用
    with open(os.path.join(PROCESSED_DIR, "green_patches_permeability.geojson"), "w", encoding="utf-8") as f:
        feats = []
        por_by_id = {r["patch_id"]: r for r in porosity}
        density_by_id = {r["patch_id"]: r for r in edge_density}
        for i, p in enumerate(patches):
            feats.append(
                {
                    "type": "Feature",
                    "geometry": p.__geo_interface__,
                    "properties": {
                        "patch_id": i,
                        "area_m2": round(p.area, 1),
                        "porosity_index_per_100m_edge": por_by_id[i]["porosity_index_per_100m_edge"],
                        "buildings_per_100m_perimeter": density_by_id[i]["buildings_per_100m_perimeter"],
                    },
                }
            )
        json.dump({"type": "FeatureCollection", "features": feats}, f, ensure_ascii=False)

    print(json.dumps({k: v for k, v in result.items() if k != "CAVEAT"}, ensure_ascii=False, indent=2)[:3000])


if __name__ == "__main__":
    main()
