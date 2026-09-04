"""共用地圖底圖與工具函式,四張分析圖都會用到。"""

import json
import os

import folium

from config import PROCESSED_DIR
from gis_utils import proj_to_wgs84


def load(name):
    with open(os.path.join(PROCESSED_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def base_map(center=(25.05, 121.52), zoom=14):
    m = folium.Map(location=list(center), zoom_start=zoom, tiles="cartodbpositron")
    boundary = load("site_boundary.geojson")
    folium.GeoJson(
        boundary,
        name="基地 2km 緩衝範圍",
        style_function=lambda x: {"color": "#d62728", "weight": 2.5, "fill": False},
    ).add_to(m)
    corridor = load("site_corridor_line.geojson")
    folium.GeoJson(
        corridor,
        name="市民大道西段路廊(近似)",
        style_function=lambda x: {"color": "#555", "weight": 2, "dashArray": "3,4"},
    ).add_to(m)
    return m


def save(m, filename, add_layer_control=True):
    if add_layer_control:
        folium.LayerControl(collapsed=False).add_to(m)
    out_dir = os.path.abspath(os.path.join(PROCESSED_DIR, "..", "..", "output"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    m.save(out_path)
    print("saved:", out_path)
    return out_path


def proj_feature_collection_to_wgs84(fc):
    """features whose geometry coordinates are in EPSG:3826 -> WGS84, in place-ish (returns new dict)."""

    def conv_coords(coords):
        if isinstance(coords[0], (int, float)):
            lon, lat = proj_to_wgs84(coords[0], coords[1])
            return [lon, lat]
        return [conv_coords(c) for c in coords]

    out_feats = []
    for f in fc["features"]:
        g = f["geometry"]
        out_feats.append(
            {
                "type": "Feature",
                "geometry": {"type": g["type"], "coordinates": conv_coords(g["coordinates"])},
                "properties": f["properties"],
            }
        )
    return {"type": "FeatureCollection", "features": out_feats}
