"""出圖②:街區特色——土地使用分區(概化大類)+ 建物密度網格 + 近年建照。

建物密度網格只涵蓋目前已收到的建物圖磚範圍(約基地 94.7%,見 analysis2 的
building_footprints.coverage_note),沒資料的角落網格是空的,不代表那裡沒建物。
"""

import folium

from map_utils import base_map, load, proj_feature_collection_to_wgs84, save

GROUP_COLORS = {
    "住宅": "#fdd0a2",
    "商業": "#e6550d",
    "文教": "#9ecae1",
    "公園綠地": "#2ca02c",
    "交通": "#969696",
    "機關/行政": "#756bb1",
    "其他": "#dadaeb",
}


def categorize(zone):
    if not zone:
        return "其他"
    if "住宅" in zone:
        return "住宅"
    if "商業" in zone:
        return "商業"
    if any(k in zone for k in ["文教", "國小", "國中", "高中", "大專", "圖書館"]):
        return "文教"
    if any(k in zone for k in ["公園", "綠地", "河川", "保護"]):
        return "公園綠地"
    if any(k in zone for k in ["交通", "道路", "廣場", "停車", "鐵路"]):
        return "交通"
    if any(k in zone for k in ["機關", "行政", "市場"]):
        return "機關/行政"
    return "其他"


def main():
    m = base_map()

    zoning = proj_feature_collection_to_wgs84(load("zoning_細部計畫_clipped.geojson"))
    zoning_layer = folium.FeatureGroup(name="土地使用分區(概化大類)")
    folium.GeoJson(
        zoning,
        style_function=lambda x: {
            "color": GROUP_COLORS[categorize(x["properties"].get("使用分區"))],
            "fillColor": GROUP_COLORS[categorize(x["properties"].get("使用分區"))],
            "fillOpacity": 0.5,
            "weight": 0.3,
        },
        tooltip=folium.GeoJsonTooltip(fields=["使用分區"], aliases=["分區"]),
    ).add_to(zoning_layer)
    zoning_layer.add_to(m)

    density = load("building_density_grid.geojson")

    def density_color(count):
        if count < 10:
            return "#fee5d9"
        if count < 25:
            return "#fcae91"
        if count < 50:
            return "#fb6a4a"
        if count < 100:
            return "#de2d26"
        return "#a50f15"

    density_layer = folium.FeatureGroup(name="建物密度(200m 網格)")
    folium.GeoJson(
        density,
        style_function=lambda x: {
            "color": "#666",
            "weight": 0.3,
            "fillColor": density_color(x["properties"]["building_count"]),
            "fillOpacity": 0.65,
        },
        tooltip=folium.GeoJsonTooltip(fields=["building_count", "avg_height_m"], aliases=["棟數", "平均樓高(m)"]),
    ).add_to(density_layer)
    density_layer.add_to(m)

    permits = proj_feature_collection_to_wgs84(load("building_permits_clipped.geojson"))
    permit_layer = folium.FeatureGroup(name=f"近年建照({len(permits['features'])} 筆)")
    for f in permits["features"]:
        coords = f["geometry"]["coordinates"]
        # H05011 的點是 MultiPoint(每個 feature 只有一個點),不是單一 Point
        lon, lat = coords[0] if f["geometry"]["type"] == "MultiPoint" else coords
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color="#000",
            fill=True,
            fill_color="#ffeb3b",
            fill_opacity=0.9,
            weight=1,
            popup=f["properties"].get("名稱"),
        ).add_to(permit_layer)
    permit_layer.add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
                background: white; padding: 10px 14px; border: 1px solid #999;
                border-radius: 4px; font-size: 13px; line-height: 1.6;">
      <b>② 街區特色</b><br>
      <span style="color:#fdd0a2;">■</span> 住宅
      <span style="color:#e6550d;">■</span> 商業
      <span style="color:#9ecae1;">■</span> 文教
      <span style="color:#2ca02c;">■</span> 公園綠地<br>
      <span style="color:#969696;">■</span> 交通
      <span style="color:#756bb1;">■</span> 機關/行政
      <span style="color:#dadaeb;">■</span> 其他<br>
      建物密度網格未涵蓋約 5.3% 邊角(尚未取得建物資料)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    save(m, "map2_block_character.html")


if __name__ == "__main__":
    main()
