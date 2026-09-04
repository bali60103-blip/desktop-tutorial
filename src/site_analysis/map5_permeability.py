"""出圖⑤:綠帶對城市滲透性的幫助——Sennett/Gehl/Jacobs 三人論點各自的圖層。

五個可切換圖層對應 analysis5_permeability.py 的五個子分析,方法論與限制見該檔案
開頭註解跟 README。
"""

import json
import os

import folium
from shapely.geometry import shape
from shapely.ops import transform

from clip_utils import clip_features_3826, site_boundary_3826
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_shapefile_as_geojson, proj_to_wgs84, wgs84_to_proj
from map_utils import base_map, load, save


def to_wgs84(geom):
    return transform(lambda x, y: proj_to_wgs84(x, y), geom)


def color_scale(value, breaks, colors):
    for b, c in zip(breaks, colors):
        if value <= b:
            return c
    return colors[-1]


def main():
    m = base_map()
    summary = json.load(open(os.path.join(PROCESSED_DIR, "analysis5_summary.json"), encoding="utf-8"))
    patches = json.load(open(os.path.join(PROCESSED_DIR, "green_patches_permeability.geojson"), encoding="utf-8"))

    # -- 1. Sennett:邊界穿透度(porosity) --
    porosity_breaks = [0, 1, 2, 3.5, 100]
    porosity_colors = ["#f2f0f7", "#cbc9e2", "#9e9ac8", "#756bb1", "#54278f"]
    layer1 = folium.FeatureGroup(name="① Sennett 綠地邊界穿透度(每100m邊界的步行接觸點)")
    for f in patches["features"]:
        g = to_wgs84(shape(f["geometry"]))
        val = f["properties"].get("porosity_index_per_100m_edge") or 0
        folium.GeoJson(
            g.__geo_interface__,
            style_function=lambda x, v=val: {
                "fillColor": color_scale(v, porosity_breaks, porosity_colors),
                "color": "#333",
                "weight": 0.5,
                "fillOpacity": 0.8,
            },
            tooltip=f"穿透度指數: {val}",
        ).add_to(layer1)
    layer1.add_to(m)

    # -- 2. Gehl:400m/800m 步行可及性圈 --
    layer2 = folium.FeatureGroup(name="② Gehl 綠地步行可及性圈(400m/800m)", show=False)
    from shapely.ops import unary_union

    green_polys = [shape(f["geometry"]) for f in patches["features"]]
    green_union = unary_union(green_polys)
    for radius, color, op in [(800, "#a1d99b", 0.15), (400, "#31a354", 0.25)]:
        ring = to_wgs84(green_union.buffer(radius))
        folium.GeoJson(
            ring.__geo_interface__,
            style_function=lambda x, c=color, o=op: {"fillColor": c, "color": c, "weight": 1, "fillOpacity": o},
        ).add_to(layer2)
    layer2.add_to(m)

    # -- 3. Gehl:邊界緊鄰建物密度(edge effect) --
    density_breaks = [0, 2, 5, 10, 1000]
    density_colors = ["#fff5eb", "#fdbe85", "#fd8d3c", "#e6550d", "#a63603"]
    layer3 = folium.FeatureGroup(name="③ Gehl 綠地邊界緊鄰建物密度(30m內棟數/100m邊界)", show=False)
    for f in patches["features"]:
        g = to_wgs84(shape(f["geometry"]))
        val = f["properties"].get("buildings_per_100m_perimeter") or 0
        folium.GeoJson(
            g.__geo_interface__,
            style_function=lambda x, v=val: {
                "fillColor": color_scale(v, density_breaks, density_colors),
                "color": "#333",
                "weight": 0.5,
                "fillOpacity": 0.8,
            },
            tooltip=f"邊界建物密度: {val} 棟/100m",
        ).add_to(layer3)
    layer3.add_to(m)

    # -- 4. Jacobs:道路寬度分級(細街廓 vs 寬幹道) --
    layer4 = folium.FeatureGroup(name="④ Jacobs 道路寬度分級(細街廓 vs 寬幹道)", show=False)
    roads = load_shapefile_as_geojson(os.path.join(RAW_DIR, "shp", "roadsize2.shp"), encoding="utf-8")
    roads_clipped = clip_features_3826(roads["features"])

    def parse_width(w):
        try:
            return float(str(w).rstrip("M"))
        except (TypeError, ValueError):
            return None

    for f in roads_clipped:
        w = parse_width(f["properties"].get("road_width"))
        if w is None:
            continue
        if w < 8:
            color, weight = "#2166ac", 1.2
        elif w < 20:
            color, weight = "#999", 1.5
        else:
            color, weight = "#b2182b", 3
        g = to_wgs84(shape(f["geometry"]))
        folium.PolyLine(
            [[lat, lon] for lon, lat in g.coords], color=color, weight=weight, opacity=0.8
        ).add_to(layer4)
    layer4.add_to(m)

    # -- 5. Jacobs:綠地碎片化/連通(+行道樹是否真的林蔭相連) --
    layer5 = folium.FeatureGroup(
        name="⑤ Jacobs 綠地斑塊連通(綠=林蔭連結/橘=僅步道無樹/紅=無連結)", show=False
    )
    frag = summary["jacobs_green_fragmentation"]
    patch_geoms = {f["properties"]["patch_id"]: shape(f["geometry"]) for f in patches["features"]}
    for link in frag:
        p1 = patch_geoms.get(link["patch_id"])
        p2 = patch_geoms.get(link["nearest_patch_id"])
        if p1 is None or p2 is None:
            continue
        c1, c2 = to_wgs84(p1.centroid), to_wgs84(p2.centroid)
        if link.get("tree_linked"):
            color, weight, dash = "#31a354", 2.2, None
        elif link["pedestrian_link_detected"]:
            color, weight, dash = "#e6852c", 1.5, "6,4"
        else:
            color, weight, dash = "#de2d26", 1.2, "2,4"
        folium.PolyLine(
            [[c1.y, c1.x], [c2.y, c2.x]],
            color=color,
            weight=weight,
            opacity=0.75,
            dash_array=dash,
            tooltip=f"間距 {link['gap_distance_m']}m,走廊內行道樹 {link.get('trees_in_corridor', '?')} 株",
        ).add_to(layer5)
    layer5.add_to(m)

    # -- 6. 行道樹密度(供對照⑤的林蔭判斷) --
    from folium.plugins import HeatMap

    layer6 = folium.FeatureGroup(name="⑥ 行道樹密度(對照⑤的林蔭連結判斷)", show=False)
    trees = load("street_trees_clipped.geojson")
    heat_pts = []
    for f in trees["features"]:
        x, y = f["geometry"]["coordinates"]
        lon, lat = proj_to_wgs84(x, y)
        heat_pts.append([lat, lon, 1])
    HeatMap(heat_pts, radius=10, blur=8, max_zoom=16).add_to(layer6)
    layer6.add_to(m)

    legend_html = f"""
    <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
                background: white; padding: 10px 14px; border: 1px solid #999;
                border-radius: 4px; font-size: 12.5px; line-height: 1.6; max-width: 300px;">
      <b>⑤ 綠帶滲透性分析(Sennett/Gehl/Jacobs)</b><br>
      步行可及涵蓋率:400m內 {summary['gehl_walk_catchment']['within_400m_pct']}%,
      800m內 {summary['gehl_walk_catchment']['within_800m_pct']}%<br>
      細街廓道路(&lt;8m)佔比 {summary['jacobs_block_grain']['fine_grain_lt8m_pct_of_total']}%,
      寬幹道(&ge;20m)佔比 {summary['jacobs_block_grain']['wide_ge20m_pct_of_total']}%<br>
      綠地斑塊數:{summary['green_patch_count']}<br>
      斑塊最近鄰連結:步道相連 {summary['jacobs_green_fragmentation_summary']['pedestrian_linked_pct']}%,
      <b>真正林蔭相連僅 {summary['jacobs_green_fragmentation_summary']['tree_linked_pct']}%</b><br>
      <span style="color:#e6852c;">■</span> 步道相連但無樹({summary['jacobs_green_fragmentation_summary']['pedestrian_linked_but_treeless_pct']}%)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    save(m, "map5_permeability.html")


if __name__ == "__main__":
    main()
