"""出圖①:綠帶體量——都市計畫綠地分區 + 行道樹熱區(依樹高加權)。

樹木用「樹高加權熱力圖」呈現量體感,不是真正的樹冠體積(見 analysis1 的說明,
沒有樹冠寬度資料算不出真正體積),熱力圖顏色深淺代表「樹木密度 x 平均樹高」
的綜合強度,只能當作量體感的示意,不是精確數值。
"""

import folium
from folium.plugins import HeatMap

from gis_utils import proj_to_wgs84
from map_utils import base_map, load, proj_feature_collection_to_wgs84, save

ZONE_COLORS = {
    "公園用地": "#2ca02c",
    "綠地用地": "#98df8a",
    "河川區": "#6baed6",
    "保護區": "#31a354",
}


def main():
    m = base_map()

    green = proj_feature_collection_to_wgs84(load("green_zoning_細部計畫_clipped.geojson"))
    green_layer = folium.FeatureGroup(name="都市計畫綠地分區(細部計畫:公園/綠地/河川/保護區)")
    folium.GeoJson(
        green,
        style_function=lambda x: {
            "color": ZONE_COLORS.get(x["properties"].get("使用分區"), "#999"),
            "fillColor": ZONE_COLORS.get(x["properties"].get("使用分區"), "#999"),
            "fillOpacity": 0.45,
            "weight": 0.5,
        },
        tooltip=folium.GeoJsonTooltip(fields=["使用分區"], aliases=["分區"]),
    ).add_to(green_layer)
    green_layer.add_to(m)

    trees = load("street_trees_clipped.geojson")
    heat_pts = []
    for f in trees["features"]:
        x, y = f["geometry"]["coordinates"]
        lon, lat = proj_to_wgs84(x, y)
        h = f["properties"].get("TreeHeight") or 5
        heat_pts.append([lat, lon, h])
    heat_layer = folium.FeatureGroup(name=f"行道樹熱區(樹高加權,{len(heat_pts)} 株)")
    HeatMap(heat_pts, radius=12, blur=10, max_zoom=16).add_to(heat_layer)
    heat_layer.add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
                background: white; padding: 10px 14px; border: 1px solid #999;
                border-radius: 4px; font-size: 13px; line-height: 1.6;">
      <b>① 綠帶體量分析</b><br>
      <span style="color:#2ca02c;">■</span> 公園用地
      <span style="color:#98df8a;">■</span> 綠地用地
      <span style="color:#6baed6;">■</span> 河川區
      <span style="color:#31a354;">■</span> 保護區<br>
      熱區 = 行道樹密度 x 樹高加權(非真實樹冠體積)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    save(m, "map1_green_volume.html")


if __name__ == "__main__":
    main()
