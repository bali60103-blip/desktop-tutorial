"""基地紋理圖(figure-ground):建物量體(灰) + 市民大道主軸(黑) + 綠帶(綠) + 水域(藍)。

參考風格:類似都市計畫提案常見的 figure-ground 底圖(建物淡灰、綠帶飽和綠、
水域柔藍、主要軸線加粗),不是互動地圖,是給簡報/排版用的靜態精細渲染圖。

輸出 ../../output/site_figure_ground.png(高解析點陣,適合直接放簡報)與
.svg(向量,適合再匯入 Illustrator/Figma 精修)。
"""

import json
import os

import matplotlib

matplotlib.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei"]
matplotlib.rcParams["axes.unicode_minus"] = False

import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
from shapely.geometry import shape
from shapely.ops import transform

from config import PROCESSED_DIR
from gis_utils import wgs84_to_proj

BG = "#fbfbf9"
BUILDING_FILL = "#d6d6d3"
BUILDING_EDGE = "#a3a39f"
GREEN_FILL = "#5c8c4a"
WATER_FILL = "#a9cbe0"
CORRIDOR_COLOR = "#141414"
BOUNDARY_COLOR = "#3a3a3a"
CONNECTOR_COLOR = "#8a6d3b"


def load(name):
    with open(os.path.join(PROCESSED_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def to_3826_geom(geom):
    return transform(lambda lon, lat: wgs84_to_proj(lon, lat), shape(geom))


def polygon_path(poly):
    """shapely Polygon -> matplotlib Path honoring interior holes."""
    verts = list(poly.exterior.coords)
    codes = [MplPath.MOVETO] + [MplPath.LINETO] * (len(verts) - 2) + [MplPath.CLOSEPOLY]
    all_verts, all_codes = list(verts), list(codes)
    for interior in poly.interiors:
        iv = list(interior.coords)
        all_verts += iv
        all_codes += [MplPath.MOVETO] + [MplPath.LINETO] * (len(iv) - 2) + [MplPath.CLOSEPOLY]
    return MplPath(all_verts, all_codes)


def add_polygons(ax, geoms, facecolor, edgecolor=None, linewidth=0.0, zorder=1, alpha=1.0, use_holes=False):
    if use_holes:
        for g in geoms:
            polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
            for p in polys:
                ax.add_patch(
                    PathPatch(
                        polygon_path(p),
                        facecolor=facecolor,
                        edgecolor=edgecolor or "none",
                        linewidth=linewidth,
                        zorder=zorder,
                        alpha=alpha,
                    )
                )
        return
    verts = []
    for g in geoms:
        polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
        for p in polys:
            verts.append(list(p.exterior.coords))
    pc = PolyCollection(
        verts, facecolor=facecolor, edgecolor=edgecolor or "none", linewidth=linewidth, zorder=zorder, alpha=alpha
    )
    ax.add_collection(pc)


def main():
    boundary = to_3826_geom(load("site_boundary.geojson")["features"][0]["geometry"])
    minx, miny, maxx, maxy = boundary.bounds

    buildings = load("buildings_clipped.geojson")["features"]
    building_geoms = [shape(f["geometry"]) for f in buildings]

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

    fig, ax = plt.subplots(figsize=(18, 16), dpi=220)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    add_polygons(ax, water_geoms, WATER_FILL, zorder=1, use_holes=True)
    add_polygons(ax, green_geoms, GREEN_FILL, zorder=2, use_holes=True)
    add_polygons(ax, building_geoms, BUILDING_FILL, edgecolor=BUILDING_EDGE, linewidth=0.12, zorder=3)

    # 市民大道主軸(基地主軸,加粗實線 + 柔和外框強調)
    for line in corridor.geoms:
        xs, ys = line.xy
        ax.plot(xs, ys, color=CORRIDOR_COLOR, linewidth=3.4, zorder=6, solid_capstyle="round")
        ax.plot(xs, ys, color=CORRIDOR_COLOR, linewidth=9, alpha=0.12, zorder=5, solid_capstyle="round")

    # 基地邊界(虛線)
    bx, by = boundary.exterior.xy
    ax.plot(bx, by, color=BOUNDARY_COLOR, linewidth=1.3, linestyle=(0, (2, 3)), zorder=7)

    pad = 150
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)
    ax.set_aspect("equal")
    ax.axis("off")

    # 比例尺(500m)
    sx0 = minx + 200
    sy0 = miny + 200
    ax.plot([sx0, sx0 + 500], [sy0, sy0], color="#333", linewidth=2, zorder=10)
    ax.text(sx0 + 250, sy0 + 60, "500 m", ha="center", fontsize=10, color="#333", zorder=10)

    ax.set_title(
        "市民大道西段 — 華山大草原基地\n主軸與周邊綠帶紋理圖",
        fontsize=18,
        color="#222",
        pad=18,
        fontweight="bold",
    )

    out_dir = os.path.abspath(os.path.join(PROCESSED_DIR, "..", "..", "output"))
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, "site_figure_ground.png")
    svg_path = os.path.join(out_dir, "site_figure_ground.svg")
    fig.savefig(png_path, facecolor=BG, bbox_inches="tight")
    fig.savefig(svg_path, facecolor=BG, bbox_inches="tight")
    print("saved:", png_path)
    print("saved:", svg_path)


if __name__ == "__main__":
    main()
