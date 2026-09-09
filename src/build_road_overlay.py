"""Turn ../data/mingsheng_road.geojson (real OSM geometry, from
fetch_road_network.py) into a self-contained HTML page that plots 市民大道's
actual shape true-to-scale, with a lat/lon graticule and a real distance
scale bar -- so it can be checked against the real area instead of trusting
a hand-drawn schematic.

This intentionally draws ONLY the road geometry plus geographic reference
(grid + scale bar). It does not place any commercial/land-use/cognitive-map
markers -- those still need real data of their own; see data_sources.md.

Run: python build_road_overlay.py
Output: ../output/real_road_map.html
"""

import json
import math
import sys

IN_PATH = "../data/mingsheng_road.geojson"
OUT_PATH = "../output/real_road_map.html"

# Drawing area inside a 1000x620 viewBox (leaves room for header/legend/scale bar).
DRAW_X0, DRAW_Y0 = 60, 90
DRAW_W, DRAW_H = 880, 440

METERS_PER_DEG_LAT = 111320.0


def load_features():
    with open(IN_PATH, encoding="utf-8") as f:
        gj = json.load(f)
    feats = [ft for ft in gj.get("features", []) if ft["geometry"]["type"] == "LineString"]
    if not feats:
        raise ValueError("no LineString features in " + IN_PATH)
    return feats


def build_projection(feats):
    lats = [lat for ft in feats for lon, lat in ft["geometry"]["coordinates"]]
    lons = [lon for ft in feats for lon, lat in ft["geometry"]["coordinates"]]
    lat0 = (min(lats) + max(lats)) / 2
    cos0 = math.cos(math.radians(lat0))

    xs_raw = [lon * cos0 for lon in lons]
    ys_raw = lats
    xmin, xmax = min(xs_raw), max(xs_raw)
    ymin, ymax = min(ys_raw), max(ys_raw)
    width_raw = max(xmax - xmin, 1e-9)
    height_raw = max(ymax - ymin, 1e-9)

    scale = min(DRAW_W / width_raw, DRAW_H / height_raw)
    draw_w, draw_h = width_raw * scale, height_raw * scale
    off_x = DRAW_X0 + (DRAW_W - draw_w) / 2
    off_y = DRAW_Y0 + (DRAW_H - draw_h) / 2

    def proj(lon, lat):
        x = off_x + (lon * cos0 - xmin) * scale
        y = off_y + (ymax - lat) * scale
        return x, y

    meters_per_px = METERS_PER_DEG_LAT / scale
    return proj, meters_per_px, (min(lons), max(lons), min(lats), max(lats))


def path_d(coords, proj):
    pts = [proj(lon, lat) for lon, lat in coords]
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def nice_scale_length_m(meters_per_px, target_px=140):
    """Pick a round real-world distance (in meters) that draws close to target_px."""
    raw_m = target_px * meters_per_px
    magnitude = 10 ** math.floor(math.log10(raw_m))
    for mult in (1, 2, 5, 10):
        if mult * magnitude >= raw_m:
            return mult * magnitude
    return 10 * magnitude


def pick_step(span):
    """Round grid spacing (degrees) that yields roughly 4-9 lines across span."""
    if span <= 0:
        return 0.001
    for step in (0.001, 0.002, 0.005, 0.01, 0.02, 0.05):
        if span / step <= 9:
            return step
    return 0.1


def build_grid(bounds, proj):
    lon_min, lon_max, lat_min, lat_max = bounds
    lon_step = pick_step(lon_max - lon_min)
    lat_step = pick_step(lat_max - lat_min)

    lines, labels = [], []
    lon = math.ceil(lon_min / lon_step) * lon_step
    while lon <= lon_max:
        x0, y0 = proj(lon, lat_min)
        x1, y1 = proj(lon, lat_max)
        lines.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" class="grid-line" />')
        labels.append(f'<text x="{x0:.1f}" y="{DRAW_Y0 + DRAW_H + 22}" class="grid-label" text-anchor="middle">{lon:.3f}</text>')
        lon += lon_step

    lat = math.ceil(lat_min / lat_step) * lat_step
    while lat <= lat_max:
        x0, y0 = proj(lon_min, lat)
        x1, y1 = proj(lon_max, lat)
        lines.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" class="grid-line" />')
        labels.append(f'<text x="{DRAW_X0 - 10}" y="{y0:.1f}" class="grid-label" text-anchor="end" dominant-baseline="middle">{lat:.3f}</text>')
        lat += lat_step

    return "\n".join(lines + labels)


def main():
    try:
        feats = load_features()
    except FileNotFoundError:
        print(
            f"{IN_PATH} not found -- run fetch_road_network.py first "
            "(requires network access to the Overpass API; blocked in some sandboxes).",
            file=sys.stderr,
        )
        sys.exit(1)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    proj, meters_per_px, bounds = build_projection(feats)

    corridor_svg, corridor_note = "", ""
    try:
        with open("../data/corridor_polygon.json", encoding="utf-8") as f:
            corridor = json.load(f)
        ring = corridor["north"] + list(reversed(corridor["south"]))
        corridor_svg = f'<path d="{path_d(ring, proj)} Z" class="corridor-fill" />'
        corridor_note = (
            f'<p class="meta">淡色帶是 build_corridor_query.py 算出的 &plusmn;'
            f'{corridor["buffer_m"]:.0f}m 緩衝範圍(用來產生貼著真實路線的 POI 查詢),'
            f"不是路寬本身。</p>"
        )
    except FileNotFoundError:
        pass

    road_paths = "\n".join(
        f'<path d="{path_d(ft["geometry"]["coordinates"], proj)}" class="road-path" />'
        for ft in feats
    )
    lane_paths = "\n".join(
        f'<path d="{path_d(ft["geometry"]["coordinates"], proj)}" class="lane-path" />'
        for ft in feats
    )
    grid_svg = build_grid(bounds, proj)

    bar_m = nice_scale_length_m(meters_per_px)
    bar_px = bar_m / meters_per_px
    bar_x0 = DRAW_X0 + DRAW_W - bar_px
    bar_y = DRAW_Y0 + DRAW_H + 46
    bar_label = f"{bar_m:.0f} m" if bar_m < 1000 else f"{bar_m / 1000:.1f} km"

    segment_count = len(feats)

    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8" />
<title>市民大道真實路網</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
<style>
  :root {{
    --bg: #eceef0; --surface: #ffffff; --ink: #1b1f23; --ink-muted: #5b6470;
    --ink-faint: #939ba3; --border: #dadde1; --road: #34383e; --road-line: #d9b23c;
    --grid: #c7ccd1; --corridor: #6b6fc9; --shadow: 0 1px 2px rgba(20,22,25,.06), 0 10px 24px -16px rgba(20,22,25,.28);
    --radius: 12px; color-scheme: light;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #14161a; --surface: #1d2024; --ink: #edeef0; --ink-muted: #a9b0b8;
      --ink-faint: #6f767e; --border: #33373c; --road: #d9dde2; --road-line: #e0b84e;
      --grid: #33383e; --corridor: #9297e0; --shadow: 0 1px 2px rgba(0,0,0,.5), 0 10px 28px -16px rgba(0,0,0,.7);
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #14161a; --surface: #1d2024; --ink: #edeef0; --ink-muted: #a9b0b8;
    --ink-faint: #6f767e; --border: #33373c; --road: #d9dde2; --road-line: #e0b84e;
    --grid: #33383e; --corridor: #9297e0; --shadow: 0 1px 2px rgba(0,0,0,.5), 0 10px 28px -16px rgba(0,0,0,.7);
  }}
  * {{ box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--ink); font-family: "IBM Plex Sans", "Noto Sans TC", system-ui, sans-serif; line-height: 1.6; }}
  .page {{ max-width: 980px; margin: 0 auto; padding: 40px 20px 60px; display: flex; flex-direction: column; gap: 20px; }}
  h1 {{ font-family: "Archivo", "Noto Sans TC", sans-serif; font-size: clamp(1.5rem, 4vw, 2.1rem); font-weight: 800; margin: 0; text-wrap: balance; }}
  .eyebrow {{ margin: 0 0 8px; font-family: "IBM Plex Mono", monospace; font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-faint); }}
  .lede {{ max-width: 68ch; color: var(--ink-muted); font-size: .95rem; margin: 8px 0 0; }}
  .panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); padding: 18px 20px; }}
  .map-wrap {{ overflow-x: auto; }}
  svg {{ display: block; width: 100%; height: auto; min-width: 640px; }}
  .road-path {{ fill: none; stroke: var(--road); stroke-width: 9; stroke-linecap: round; stroke-linejoin: round; }}
  .lane-path {{ fill: none; stroke: var(--road-line); stroke-width: 2; stroke-dasharray: 14 10; stroke-linecap: round; }}
  .grid-line {{ stroke: var(--grid); stroke-width: 1; }}
  .corridor-fill {{ fill: var(--corridor); opacity: .16; stroke: var(--corridor); stroke-width: 1; stroke-dasharray: 5 4; }}
  .grid-label {{ font-family: "IBM Plex Mono", monospace; font-size: 10px; fill: var(--ink-faint); }}
  .scale-bar {{ stroke: var(--ink-muted); stroke-width: 2; }}
  .scale-label {{ font-family: "IBM Plex Mono", monospace; font-size: 12px; fill: var(--ink-muted); }}
  .meta {{ font-family: "IBM Plex Mono", monospace; font-size: .8rem; color: var(--ink-faint); }}
  .notes {{ font-size: .86rem; color: var(--ink-muted); }}
  .notes strong {{ color: var(--ink); }}
</style>
</head>
<body>
<div class="page">
  <header>
    <p class="eyebrow">真實地理 · OpenStreetMap</p>
    <h1>市民大道真實路網</h1>
    <p class="lede">下面是從 OpenStreetMap 取回、依真實經緯度等比例投影畫出的市民大道線型(共 {segment_count} 段 OSM way),對照下方的經緯度格線與比例尺,而不是手畫的示意直線。</p>
  </header>
  <section class="panel map-wrap">
    <svg viewBox="0 0 1000 620" role="img" aria-label="市民大道真實路網,依經緯度等比例投影">
      {grid_svg}
      {corridor_svg}
      {road_paths}
      {lane_paths}
      <line x1="{bar_x0:.1f}" y1="{bar_y}" x2="{DRAW_X0 + DRAW_W}" y2="{bar_y}" class="scale-bar" />
      <line x1="{bar_x0:.1f}" y1="{bar_y - 5}" x2="{bar_x0:.1f}" y2="{bar_y + 5}" class="scale-bar" />
      <line x1="{DRAW_X0 + DRAW_W}" y1="{bar_y - 5}" x2="{DRAW_X0 + DRAW_W}" y2="{bar_y + 5}" class="scale-bar" />
      <text x="{(bar_x0 + DRAW_X0 + DRAW_W) / 2:.1f}" y="{bar_y + 18}" text-anchor="middle" class="scale-label">{bar_label}</text>
    </svg>
  </section>
  <p class="meta">投影:等距圓柱投影(以緯度校正經度縮放),原始座標來自 OpenStreetMap way 幾何 &mdash; 不是預設的示意直線。</p>
  {corridor_note}
  <section class="panel notes">
    <p><strong>這張圖只畫路網本身。</strong>商家密度、連鎖品牌、建物樓齡、認知地圖邊界等圖層仍然需要各自的真實資料來源才能疊上去,見 <code>data_sources.md</code>。</p>
  </section>
</div>
</body>
</html>
"""

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Wrote {OUT_PATH} from {segment_count} road segments")


if __name__ == "__main__":
    main()
