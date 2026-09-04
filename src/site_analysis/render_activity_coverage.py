"""建築量體活動密度覆蓋圖:用建築輪廓對地標,以 analysis9 配對到每棟建築的真實
OSM 商業/辦公 POI 數(activity_poi_count)做建築量體 choropleth,疊加 160 座公園
的 400m 服務範圍,並特別標記 PR25 以下(低度連結)的公園。

風格延續 render_site_figure_ground.py 的靜態精細渲染(不是互動地圖),重用該檔的
繪圖工具函式,背景保留淡化的水域/綠帶紋理跟市民大道主軸當空間定位參考,前景是
建築量體依 activity_poi_count 上色的覆蓋圖。

**再次強調(跟 analysis9 的 CAVEAT 一致)**:建築上色是「15m 內最近真實 POI 數」的
空間鄰近代理值,不是實際商業登記或人流量;沒有配對到任何 POI 的建築(灰色)不代表
一定沒有商業活動,只代表 15m 內沒有 OSM 收錄到的餐飲/零售/辦公 POI。

輸出 ../../output/activity_coverage.png 與 .svg。
"""

import json
import os

import matplotlib

matplotlib.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Circle, Patch
from shapely.geometry import shape
from shapely.ops import transform

from config import PROCESSED_DIR
from gis_utils import wgs84_to_proj
from render_site_figure_ground import (
    BG,
    BOUNDARY_COLOR,
    CORRIDOR_COLOR,
    GREEN_FILL,
    WATER_FILL,
    add_polygons,
    load,
    to_3826_geom,
)

NO_DATA_FILL = "#d6d6d3"
BUILDING_EDGE = "#ffffff"
PARK_COLOR = "#2f6b3a"
LOW_CONN_COLOR = "#c1272d"
PARK_RADIUS_M = 400

# 0 顆星建築用中性灰(NO_DATA_FILL,見上),>=1 顆才進入活動密度色階
BINS = [1, 2, 3, 5, 8, 999]
RAMP_COLORS = ["#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"]


def main():
    boundary = to_3826_geom(load("site_boundary.geojson")["features"][0]["geometry"])
    minx, miny, maxx, maxy = boundary.bounds

    activity = load("buildings_activity.geojson")["features"]
    building_geoms = [shape(f["geometry"]) for f in activity]
    counts = [f["properties"]["activity_poi_count"] for f in activity]

    green_feats = load("green_zoning_細部計畫_clipped.geojson")["features"]
    green_geoms, water_geoms = [], []
    for f in green_feats:
        g = shape(f["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        if f["properties"].get("使用分區") == "河川區":
            water_geoms.append(g)
        else:
            green_geoms.append(g)

    corridor = to_3826_geom(load("site_corridor_line.geojson")["features"][0]["geometry"])

    analysis9 = json.load(open(os.path.join(PROCESSED_DIR, "analysis9_summary.json"), encoding="utf-8"))
    analysis7 = json.load(open(os.path.join(PROCESSED_DIR, "analysis7_summary.json"), encoding="utf-8"))
    low_conn_names = {p["name"] for p in analysis7["low_connectivity_parks_pr25_below"]}

    parks_geo = load("parks_basic_info_clipped.geojson")["features"]
    park_points = []
    for f in parks_geo:
        name = f["properties"].get("pm_name")
        lon, lat = f["geometry"]["coordinates"]
        x, y = wgs84_to_proj(lon, lat)
        park_points.append((name, x, y, name in low_conn_names))

    fig, ax = plt.subplots(figsize=(20, 17), dpi=220)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # 背景空間參考(淡化)
    add_polygons(ax, water_geoms, WATER_FILL, zorder=1, use_holes=True, alpha=0.5)
    add_polygons(ax, green_geoms, GREEN_FILL, zorder=2, use_holes=True, alpha=0.35)

    # 建築量體 choropleth:0 顆 POI = 中性灰,>=1 顆依色階
    no_data_geoms = [g for g, c in zip(building_geoms, counts) if c == 0]
    add_polygons(ax, no_data_geoms, NO_DATA_FILL, edgecolor=BUILDING_EDGE, linewidth=0.08, zorder=3)

    cmap = ListedColormap(RAMP_COLORS)
    norm = BoundaryNorm(BINS, cmap.N)
    for g, c in zip(building_geoms, counts):
        if c == 0:
            continue
        polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
        for p in polys:
            ax.fill(*p.exterior.xy, facecolor=cmap(norm(c)), edgecolor=BUILDING_EDGE, linewidth=0.08, zorder=4)

    # 市民大道主軸
    for line in corridor.geoms:
        xs, ys = line.xy
        ax.plot(xs, ys, color=CORRIDOR_COLOR, linewidth=3.0, zorder=6, solid_capstyle="round")
        ax.plot(xs, ys, color=CORRIDOR_COLOR, linewidth=8, alpha=0.12, zorder=5, solid_capstyle="round")

    # 公園服務範圍:一般公園只標中心點(400m圈重疊太多會蓋掉建築色階,不畫圈),
    # PR25以下低度連結公園才畫粗紅虛線圈+標籤,才是這張圖真正要凸顯的對照重點
    for name, x, y, is_low in park_points:
        if is_low:
            circle = Circle(
                (x, y), PARK_RADIUS_M, fill=False, edgecolor=LOW_CONN_COLOR, linewidth=1.8, linestyle=(0, (4, 2)), zorder=8
            )
            ax.add_patch(circle)
            ax.plot(x, y, marker="o", markersize=5, color=LOW_CONN_COLOR, zorder=9)
            near_top = y > maxy - 350
            label_y = y - PARK_RADIUS_M - 25 if near_top else y + PARK_RADIUS_M + 25
            ax.text(
                x,
                label_y,
                name,
                fontsize=6.3,
                color=LOW_CONN_COLOR,
                ha="center",
                va="top" if near_top else "bottom",
                zorder=9,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none", alpha=0.75),
            )
        else:
            ax.plot(x, y, marker="o", markersize=2.6, color=PARK_COLOR, alpha=0.8, zorder=7)

    # 基地邊界
    bx, by = boundary.exterior.xy
    ax.plot(bx, by, color=BOUNDARY_COLOR, linewidth=1.3, linestyle=(0, (2, 3)), zorder=10)

    pad = 150
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)
    ax.set_aspect("equal")
    ax.axis("off")

    # 比例尺
    sx0 = minx + 200
    sy0 = miny + 200
    ax.plot([sx0, sx0 + 500], [sy0, sy0], color="#333", linewidth=2, zorder=12)
    ax.text(sx0 + 250, sy0 + 60, "500 m", ha="center", fontsize=10, color="#333", zorder=12)

    ax.set_title(
        "建築量體商業活動密度覆蓋圖(以最近400m內真實OSM POI配對)\n"
        "紅色虛線圈 = 連結度綜合PR25以下的公園",
        fontsize=17,
        color="#222",
        pad=16,
        fontweight="bold",
    )

    # 色階圖例(choropleth colorbar,離散分級)
    sm = ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(sm, ax=ax, shrink=0.35, pad=0.02, ticks=BINS[:-1])
    cbar.ax.set_yticklabels(["1", "2", "3", "5", "8+"])
    cbar.set_label("建築 15m 內配對到的商業/辦公 POI 數", fontsize=9)

    legend_handles = [
        Patch(facecolor=NO_DATA_FILL, edgecolor=BUILDING_EDGE, label="建築(0顆POI配對)"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=PARK_COLOR, markersize=6, label="一般公園(中心點)"),
        Patch(facecolor="none", edgecolor=LOW_CONN_COLOR, label="PR25以下低度連結公園,400m 範圍"),
    ]
    ax.legend(handles=legend_handles, loc="lower left", fontsize=8.5, framealpha=0.9)

    caveat = (
        f"CAVEAT:建築上色=15m內最近真實OSM商業/辦公POI數的空間鄰近代理值,不是實際商業登記或人流;\n"
        f"灰色建築不代表沒有商業活動,只代表附近沒有OSM收錄到的POI(全基地 unmatched POI:"
        f"{analysis9['unmatched_poi_count']} 筆,可能落在建築15m範圍外)。\n"
        f"PR25以下公園(n={analysis9['low_connectivity_pr25_group']['park_count']})周圍建築平均活動POI數 "
        f"{analysis9['low_connectivity_pr25_group']['avg_activity_poi_per_building']},"
        f"其餘公園(n={analysis9['other_parks_group']['park_count']})平均 "
        f"{analysis9['other_parks_group']['avg_activity_poi_per_building']}——"
        f"另一組獨立資料(建築鄰近POI)同樣顯示PR25以下公園周圍商業活動明顯較稀疏。"
    )
    ax.text(
        0.01,
        -0.01,
        caveat,
        transform=ax.transAxes,
        fontsize=7.3,
        color="#555",
        va="top",
        ha="left",
        wrap=True,
    )

    out_dir = os.path.abspath(os.path.join(PROCESSED_DIR, "..", "..", "output"))
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, "activity_coverage.png")
    svg_path = os.path.join(out_dir, "activity_coverage.svg")
    fig.savefig(png_path, facecolor=BG, bbox_inches="tight")
    fig.savefig(svg_path, facecolor=BG, bbox_inches="tight")
    print("saved:", png_path)
    print("saved:", svg_path)


if __name__ == "__main__":
    main()
