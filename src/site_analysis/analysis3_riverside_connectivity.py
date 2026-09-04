"""③ 找出綠帶跟延平河濱公園連結的可行性。

做法與限制說明(先講清楚,再看數字):
- 這裡沒有道路路網圖(node/edge graph),做不了真正的最短路徑/路網繞行分析。
- 改用「概略直線廊帶」做法:從市民大道西端(基地北緣附近)畫一條假想直線到延平河濱
  公園,再看沿線 300 公尺內,現有的人行道/標線型人行道/無障礙坡道/天橋/地下道
  分布密不密。這只能看出「這條路廊上有沒有既有步行基礎設施」的粗略訊號,
  不是實際可走的路徑規劃,真正可行性還是要實地或用路網資料做路徑分析才準。
- 延平河濱公園本身在資料裡只有一個中心點座標+概略面積,沒有公園邊界多邊形,
  所以沒辦法算「基地到公園邊界」的精確距離,只能算到公園中心點的距離。
- 行道樹另外用兩種寬度計算:300m(跟其他設施同一個寬鬆廊帶,看「這一帶整體有沒有
  樹」)+ 30m(貼近道路的緊窄帶,看「路線本身是不是真的林蔭」)。兩個數字差很多的話
  代表「這一區有樹」但「這條特定路線未必走得到樹蔭下」,是兩件事。
"""

import csv
import json
import os

from shapely.geometry import LineString, Point, shape
from shapely.ops import transform

from clip_utils import clip_features_3826, clip_points_xy, site_boundary_3826
from config import (
    CORRIDOR_WEST_LAT,
    CORRIDOR_WEST_LON,
    PROCESSED_DIR,
    RAW_DIR,
    YANPING_RIVERSIDE_PARK_LAT,
    YANPING_RIVERSIDE_PARK_LON,
)
from gis_utils import load_geojson, load_shapefile_as_geojson, proj_to_wgs84, wgs84_to_proj

CORRIDOR_CHECK_BUFFER_M = 300


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # -- 基地內既有步行/無障礙基礎設施總量 --
    sidewalks = load_geojson(os.path.join(RAW_DIR, "sidewalks.json"))
    sidewalks_clipped = clip_features_3826(sidewalks["features"])
    sidewalk_len_m = sum(shape(f["geometry"]).length for f in sidewalks_clipped)

    painted = load_shapefile_as_geojson(os.path.join(RAW_DIR, "shp", "grapline_21_15.shp"), encoding="utf-8")
    painted_clipped = clip_features_3826(painted["features"])
    painted_len_m = sum(shape(f["geometry"]).length for f in painted_clipped)

    ramps = load_geojson(os.path.join(RAW_DIR, "accessibility_ramps.json"))
    ramp_records = [f["properties"] for f in ramps["features"]]
    for r, f in zip(ramp_records, ramps["features"]):
        pt = f["geometry"]["coordinates"]
        r["_x"], r["_y"] = pt[0], pt[1]
    ramps_in_site = clip_points_xy(ramp_records, "_x", "_y")

    footbridges = load_geojson(os.path.join(RAW_DIR, "footbridges.json"))
    fb_records = [{"_x": f["Obj_Longitude"], "_y": f["Obj_Latitude"], "name": f["Footbridge_name"]} for f in footbridges]
    # footbridges are in WGS84 (lon/lat) per Obj_Longitude/Obj_Latitude — reproject before clipping
    for r in fb_records:
        r["_x"], r["_y"] = wgs84_to_proj(r["_x"], r["_y"])
    footbridges_in_site = clip_points_xy(fb_records, "_x", "_y")

    underpasses = load_geojson(os.path.join(RAW_DIR, "underpasses.json"))
    up_records = [{"_x": u["Obj_Longitude"], "_y": u["Obj_Latitude"], "name": u["Nether_name"]} for u in underpasses]
    for r in up_records:
        r["_x"], r["_y"] = wgs84_to_proj(r["_x"], r["_y"])
    underpasses_in_site = clip_points_xy(up_records, "_x", "_y")

    # -- 行道樹 --
    with open(os.path.join(RAW_DIR, "street_trees.csv"), encoding="utf-8") as f:
        tree_rows = list(csv.DictReader(f))
    for r in tree_rows:
        try:
            r["_x"], r["_y"] = float(r["TWD97X"]), float(r["TWD97Y"])
        except (TypeError, ValueError):
            r["_x"] = r["_y"] = None
    tree_rows = [r for r in tree_rows if r["_x"] is not None]
    trees_in_site = clip_points_xy(tree_rows, "_x", "_y")
    tree_pts_all = [Point(r["_x"], r["_y"]) for r in tree_rows]

    # -- 概略連結廊帶:市民大道西端 -> 延平河濱公園 --
    west_proj = wgs84_to_proj(CORRIDOR_WEST_LON, CORRIDOR_WEST_LAT)
    park_proj = wgs84_to_proj(YANPING_RIVERSIDE_PARK_LON, YANPING_RIVERSIDE_PARK_LAT)
    connector_line = LineString([west_proj, park_proj])
    connector_buffer = connector_line.buffer(CORRIDOR_CHECK_BUFFER_M)
    connector_buffer_tight = connector_line.buffer(30)

    def count_within_corridor(geoms, buf=connector_buffer):
        return sum(1 for g in geoms if buf.intersects(g))

    sidewalk_geoms_all = [shape(f["geometry"]) for f in sidewalks["features"]]
    painted_geoms_all = [shape(f["geometry"]) for f in painted["features"]]
    ramp_pts_all = [Point(r["_x"], r["_y"]) for r in ramp_records]
    fb_pts_all = [Point(r["_x"], r["_y"]) for r in fb_records]
    up_pts_all = [Point(r["_x"], r["_y"]) for r in up_records]

    trees_near_corridor_300m = count_within_corridor(tree_pts_all)
    trees_near_corridor_30m = count_within_corridor(tree_pts_all, connector_buffer_tight)
    corridor_len_km = connector_line.length / 1000

    corridor_signal = {
        "sidewalk_segments_near_corridor": count_within_corridor(sidewalk_geoms_all),
        "painted_sidewalk_segments_near_corridor": count_within_corridor(painted_geoms_all),
        "accessibility_ramps_near_corridor": count_within_corridor(ramp_pts_all),
        "footbridges_near_corridor": count_within_corridor(fb_pts_all),
        "underpasses_near_corridor": count_within_corridor(up_pts_all),
        "street_trees_within_300m_of_corridor": trees_near_corridor_300m,
        "street_trees_within_30m_of_corridor": trees_near_corridor_30m,
        "street_trees_within_30m_per_km": round(trees_near_corridor_30m / corridor_len_km, 1)
        if corridor_len_km
        else None,
        "tree_shade_note": (
            "30m內株數遠低於300m內株數,代表這一帶雖然有樹,但這條特定路線本身未必"
            "林蔭——樹木密度落差越大,越可能是路線需要調整才能真正走在樹蔭下"
            if trees_near_corridor_300m and trees_near_corridor_30m / max(trees_near_corridor_300m, 1) < 0.15
            else "30m內株數佔300m內比例不低,這條路線本身沿線有一定行道樹覆蓋"
        ),
        "connector_line_length_m": round(connector_line.length, 0),
        "corridor_check_buffer_m": CORRIDOR_CHECK_BUFFER_M,
    }

    connector_wgs84 = transform(lambda x, y: proj_to_wgs84(x, y), connector_line)
    with open(os.path.join(PROCESSED_DIR, "connector_to_yanping_park.geojson"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": list(connector_wgs84.coords)},
                        "properties": {
                            "name": "市民大道西端—延平河濱公園 概略直線廊帶(非實際路徑)",
                            "length_m": round(connector_line.length, 0),
                        },
                    }
                ],
            },
            f,
            ensure_ascii=False,
        )

    result = {
        "CAVEAT": (
            "無路網 graph 資料,無法做最短路徑分析;connector_corridor_signal 只是"
            f"沿一條假想直線(市民大道西端到延平河濱公園,長 {round(connector_line.length/1000,2)} 公里)"
            f"左右 {CORRIDOR_CHECK_BUFFER_M} 公尺內既有設施數量的粗略訊號,不是真正可走的路徑。"
            "延平河濱公園只有中心點座標,無公園邊界,故距離量到中心點。"
        ),
        "site_pedestrian_infrastructure_totals": {
            "sidewalk_length_m_in_site": round(sidewalk_len_m, 0),
            "painted_sidewalk_length_m_in_site": round(painted_len_m, 0),
            "accessibility_ramps_in_site": len(ramps_in_site),
            "footbridges_in_site": len(footbridges_in_site),
            "underpasses_in_site": len(underpasses_in_site),
            "street_trees_in_site": len(trees_in_site),
        },
        "connector_corridor_signal_to_yanping_park": corridor_signal,
    }
    with open(os.path.join(PROCESSED_DIR, "analysis3_summary.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
