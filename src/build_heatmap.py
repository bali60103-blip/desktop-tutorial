"""Turn ../data/mrt_hourly.csv into an interactive 24-hour heatmap.

Renders one Leaflet heat-layer frame per hour (0-23) with a time slider,
using folium's HeatMapWithTime. Point weights come from MRT station
entry+exit counts as a proxy for pedestrian activity -- see
../data_sources.md for what this does and doesn't represent.

Run: python build_heatmap.py
Output: ../output/heatmap.html
"""

import csv
import sys
from collections import defaultdict

import folium
from folium.plugins import HeatMapWithTime

from config import CENTER_LAT, CENTER_LON, MRT_STATIONS

STATION_COORDS = {s.name: (s.lat, s.lon) for s in MRT_STATIONS}
IN_PATH = "../data/mrt_hourly.csv"
OUT_PATH = "../output/heatmap.html"


def load_hourly_points():
    """Returns {hour_str: [[lat, lon, weight], ...]} for hours "00".."23"."""
    by_hour = defaultdict(list)
    with open(IN_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            coords = STATION_COORDS.get(row["station"])
            if not coords:
                continue
            weight = int(row.get("entries") or 0) + int(row.get("exits") or 0)
            if weight <= 0:
                continue
            hour = str(row["hour"]).zfill(2)
            by_hour[hour].append([coords[0], coords[1], weight])
    return by_hour


def main():
    try:
        by_hour = load_hourly_points()
    except FileNotFoundError:
        print(
            f"{IN_PATH} not found -- run fetch_mrt_hourly.py first "
            "(requires network access to data.taipei).",
            file=sys.stderr,
        )
        sys.exit(1)

    hours = [f"{h:02d}" for h in range(24)]
    frames = [by_hour.get(h, []) for h in hours]

    if not any(frames):
        print("No data points for any hour -- check ../data/mrt_hourly.csv", file=sys.stderr)
        sys.exit(1)

    # normalize weights per-frame so HeatMap's default radius/gradient reads sensibly
    max_w = max((p[2] for frame in frames for p in frame), default=1)
    norm_frames = [[[lat, lon, w / max_w] for lat, lon, w in frame] for frame in frames]

    m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=15, tiles="cartodbpositron")
    folium.Circle(
        location=[CENTER_LAT, CENTER_LON],
        radius=2000,
        color="#3388ff",
        fill=False,
        dash_array="4",
        tooltip="2km radius around 市民大道一段 centroid",
    ).add_to(m)

    HeatMapWithTime(
        norm_frames,
        index=[f"{h}:00" for h in hours],
        radius=35,
        auto_play=False,
        max_opacity=0.8,
    ).add_to(m)

    m.save(OUT_PATH)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
