"""出圖⑦:公園設施類型 x 400m 內可能連結的設施/商店/人潮。

一般商店沒有實際 POI,商業/市場用地分區當代理;運動/健身類商家現在有真實 POI
(585筆體育署運動產業登記資料),見 analysis7 的 CAVEAT。
"""

import json
import os

import folium
from folium.plugins import MarkerCluster
from shapely.geometry import Point

from clip_utils import site_boundary_3826
from config import PROCESSED_DIR, RAW_DIR
from gis_utils import load_geojson, proj_to_wgs84, wgs84_to_proj
from map_utils import base_map, load, proj_feature_collection_to_wgs84, save

SPORT_TYPE_COLORS = {
    "健身房": "#08519c",
    "游泳": "#3182bd",
    "體適能": "#6baed6",
    "瑜珈": "#9ecae1",
    "市民運動中心": "#08306b",
}

TAG_COLORS = {
    "銀髮健身": "#3182bd",
    "兒童遊戲": "#e6550d",
    "運動場館": "#31a354",
    "廣場集會": "#756bb1",
    "其他/未分類": "#969696",
}


def main():
    m = base_map()
    summary = json.load(open(os.path.join(PROCESSED_DIR, "analysis7_summary.json"), encoding="utf-8"))

    commercial_layer = folium.FeatureGroup(name="商業區/市場用地分區(400m連結分析的背景參考)")
    zoning = proj_feature_collection_to_wgs84(load("crowd_zoning_細部計畫_clipped.geojson"))
    for f in zoning["features"]:
        cat = f["properties"].get("使用分區")
        if cat not in {"商業區", "市場用地"} and (not cat or "商業區" not in cat):
            continue
        color = "#fdae6b" if cat == "市場用地" else "#fee5d9"
        folium.GeoJson(
            f, style_function=lambda x, c=color: {"fillColor": c, "color": c, "weight": 0.3, "fillOpacity": 0.5}
        ).add_to(commercial_layer)
    commercial_layer.add_to(m)

    park_layer = folium.FeatureGroup(name=f"公園({summary['parks_analyzed']}座,依設施類型上色)+400m連結圈")
    parks_geo = load("parks_basic_info_clipped.geojson")
    detail_by_name = {p["name"]: p for p in summary["park_details"]}
    for f in parks_geo["features"]:
        name = f["properties"].get("pm_name")
        d = detail_by_name.get(name)
        if not d:
            continue
        lon, lat = f["geometry"]["coordinates"]
        primary_tag = d["facility_tags"][0]
        color = TAG_COLORS.get(primary_tag, "#999")
        nb = d["nearby_400m"]
        popup = (
            f"<b>{name}</b>({'/'.join(d['facility_tags'])})<br>"
            f"400m內:捷運站 {nb['mrt_station_count']}(={', '.join(nb['mrt_stations']) or '無'})<br>"
            f"停車位 {nb['parking_spaces']}(共{nb['parking_lots']}處)<br>"
            f"商業區面積 {nb['commercial_zoning_area_m2']:.0f}m² / 市場用地 {nb['market_zoning_area_m2']:.0f}m²"
        )
        folium.Circle(
            location=[lat, lon], radius=400, color=color, weight=1, fill=False, opacity=0.35
        ).add_to(park_layer)
        folium.CircleMarker(
            location=[lat, lon], radius=5, color=color, fill=True, fill_opacity=0.9, popup=popup
        ).add_to(park_layer)
    park_layer.add_to(m)

    sports_biz_layer = MarkerCluster(name=f"運動/健身商家(真實POI,{summary['sports_businesses_in_site_total']}間)")
    for b in load_geojson(os.path.join(RAW_DIR, "sports_businesses.json")):
        try:
            lat, lon = float(b["Latitude"]), float(b["Longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        x, y = wgs84_to_proj(lon, lat)
        if not site_boundary_3826().contains(Point(x, y)):
            continue
        tp = b.get("SportType1")
        color = SPORT_TYPE_COLORS.get(tp, "#c6dbef")
        name = b.get("CompanyName2") or b.get("CompanyName1")
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=f"{name}({tp})<br>{b.get('Address1', '')}",
        ).add_to(sports_biz_layer)
    sports_biz_layer.add_to(m)

    mrt_layer = folium.FeatureGroup(name="捷運站")
    stations = load("mrt_stations_clipped.geojson")
    for f in stations["features"]:
        x, y = f["geometry"]["coordinates"]
        lon, lat = proj_to_wgs84(x, y)
        folium.Marker(
            [lat, lon], icon=folium.Icon(color="darkblue", icon="train", prefix="fa"), popup=f["properties"].get("NAME")
        ).add_to(mrt_layer)
    mrt_layer.add_to(m)

    ts = summary["summary_by_facility_type"]
    rows = "".join(
        f"<tr><td>{tag}</td><td>{s['park_count']}</td><td>{s['pct_with_mrt_within_400m']}%</td>"
        f"<td>{s['avg_commercial_zoning_area_m2']:.0f}</td><td>{s['avg_parking_spaces_within_400m']:.0f}</td>"
        f"<td>{s['avg_sports_businesses_within_400m']}</td></tr>"
        for tag, s in ts.items()
    )
    legend_html = f"""
    <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
                background: white; padding: 10px 14px; border: 1px solid #999;
                border-radius: 4px; font-size: 11.5px; line-height: 1.5; max-width: 480px;">
      <b>⑦ 公園設施類型 x 400m 內連結設施/人潮</b>
      (一般商店無POI,商業區面積為代理指標;運動健身商家為真實POI,
      基地內共 {summary['sports_businesses_in_site_total']} 間)
      <table style="border-collapse:collapse; margin-top:4px;">
        <tr style="font-weight:bold;"><td>類型</td><td>座數</td><td>捷運400m內</td>
        <td>平均商業區(m²)</td><td>平均車位</td><td>平均運動商家數</td></tr>
        {rows}
      </table>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    save(m, "map7_park_neighborhood.html")


if __name__ == "__main__":
    main()
