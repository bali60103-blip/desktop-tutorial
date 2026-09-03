"""Take one snapshot of YouBike 2.0 Taipei real-time station data and
append it to a running CSV log.

Source: YouBike2.0臺北市公共自行車即時資訊 (real-time only -- there is no
published historical "hourly flow" feed for YouBike, unlike the MRT
dataset). To build an hourly activity picture you need to run this script
once per hour (e.g. via cron or a GitHub Actions schedule) for a full day,
then diff consecutive snapshots' `available_rent_bikes` per station as a
proxy for borrow/return activity.

Public JSON endpoint (as published via data.taipei / data.gov.tw):
  https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json

NOTE ON VERIFICATION: this sandbox's network egress policy blocks this
exact host too (confirmed: `CONNECT tunnel failed, response 403`), so the
request below could not be exercised end-to-end from here. The endpoint
and field names come from data.gov.tw's published dataset description
(https://data.gov.tw/dataset/137993) -- double check the response shape
against that page or a browser fetch before trusting field names blindly.

Run: python poll_youbike.py
Output: appends to ../data/youbike_snapshots.csv
"""

import csv
import os
import sys
from datetime import datetime, timezone

import requests

from stations import haversine_km
from config import CENTER_LAT, CENTER_LON, RADIUS_KM

YOUBIKE_URL = "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
OUT_PATH = "../data/youbike_snapshots.csv"


def main():
    try:
        resp = requests.get(YOUBIKE_URL, timeout=30)
        resp.raise_for_status()
        stations = resp.json()
    except requests.RequestException as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        print(
            "If this is a 403/connection error, your network may be blocking "
            "this host -- this happens inside restricted sandboxes.",
            file=sys.stderr,
        )
        sys.exit(1)

    now = datetime.now(timezone.utc).isoformat()
    write_header = not os.path.exists(OUT_PATH)

    with open(OUT_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(
                ["timestamp_utc", "station_name", "lat", "lon", "available_bikes", "available_docks"]
            )

        kept = 0
        for s in stations:
            lat, lon = float(s.get("latitude", 0)), float(s.get("longitude", 0))
            if haversine_km(CENTER_LAT, CENTER_LON, lat, lon) > RADIUS_KM:
                continue
            writer.writerow(
                [
                    now,
                    s.get("sna") or s.get("station_name"),
                    lat,
                    lon,
                    s.get("available_rent_bikes"),
                    s.get("available_return_bikes"),
                ]
            )
            kept += 1

    print(f"Appended {kept} in-radius station snapshots to {OUT_PATH}")


if __name__ == "__main__":
    main()
