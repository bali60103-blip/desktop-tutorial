"""產生一張總覽地圖(Leaflet/folium),疊合基地邊界、綠地、捷運站、延平河濱連結廊帶。

這是給人看的概覽圖,不是最終分析成果圖——四項分析各自的完整資料在
../../data/processed/ 底下的 GeoJSON,可以另外用 QGIS 等工具做更細的圖面。
"""

import json
import os

import folium

from config import HUASHAN_LAWN_LAT, HUASHAN_LAWN_LON, PROCESSED_DIR, YANPING_RIVERSIDE_PARK_LAT, YANPING_RIVERSIDE_PARK_LON


def load(name):
    with open(os.path.join(PROCESSED_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def main():
    m = folium.Map(location=[25.06, 121.52], zoom_start=13, tiles="cartodbpositron")

    boundary = load("site_boundary.geojson")
    folium.GeoJson(
        boundary,
        name="基地 2km 緩衝範圍",
        style_function=lambda x: {"color": "#d62728", "weight": 2, "fill": False},
    ).add_to(m)

    corridor = load("site_corridor_line.geojson")
    folium.GeoJson(
        corridor,
        name="市民大道西段路廊(近似)",
        style_function=lambda x: {"color": "#1f77b4", "weight": 3},
    ).add_to(m)

    connector = load("connector_to_yanping_park.geojson")
    folium.GeoJson(
        connector,
        name="市民大道西端—延平河濱公園 概略連結廊帶(非實際路徑)",
        style_function=lambda x: {"color": "#9467bd", "weight": 2, "dashArray": "6,6"},
    ).add_to(m)

    parks_layer = folium.FeatureGroup(name="公園/綠地(J0301+L02015)")
    for fname, color in [
        ("green_公園綠地(J0301)_clipped.geojson", "#2ca02c"),
        ("green_公園用地分區(L02015)_clipped.geojson", "#98df8a"),
    ]:
        try:
            d = load(fname)
        except FileNotFoundError:
            continue
        folium.GeoJson(d, style_function=lambda x, c=color: {"color": c, "fillColor": c, "fillOpacity": 0.4, "weight": 1}).add_to(
            parks_layer
        )
    parks_layer.add_to(m)

    stations = load("mrt_stations_clipped.geojson")
    station_layer = folium.FeatureGroup(name="捷運站")
    for f in stations["features"]:
        # station coords are EPSG:3826; reproject for display
        from gis_utils import proj_to_wgs84

        x, y = f["geometry"]["coordinates"]
        lon, lat = proj_to_wgs84(x, y)
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color="#ff7f0e",
            fill=True,
            fill_opacity=0.9,
            popup=f["properties"].get("NAME"),
        ).add_to(station_layer)
    station_layer.add_to(m)

    folium.Marker(
        [YANPING_RIVERSIDE_PARK_LAT, YANPING_RIVERSIDE_PARK_LON],
        popup="延平河濱公園",
        icon=folium.Icon(color="green", icon="tree", prefix="fa"),
    ).add_to(m)
    folium.Marker(
        [HUASHAN_LAWN_LAT, HUASHAN_LAWN_LON],
        popup="華山大草皮(中央藝文公園)",
        icon=folium.Icon(color="orange", icon="tree", prefix="fa"),
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    out_dir = os.path.abspath(os.path.join(PROCESSED_DIR, "..", "..", "output"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "site_overview_map.html")
    m.save(out_path)
    print("saved:", out_path)


if __name__ == "__main__":
    main()
