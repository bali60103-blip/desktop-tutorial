"""Fetch Taipei MRT hourly station entry/exit counts from data.taipei and
filter down to stations within 2km of 市民大道一段.

Dataset: 臺北捷運各站分時進出量統計OD (Taipei MRT hourly station
entry/exit volume by O-D), published on data.taipei:
  https://data.taipei/dataset/detail?id=63f31c7e-7fc3-418b-bd82-b95158755b4d

NOTE ON VERIFICATION: this script was written from a sandboxed environment
whose network egress policy blocks data.taipei outright (confirmed via a
direct connection test: `CONNECT tunnel failed, response 403`), so the
exact resource id and JSON column names below could NOT be confirmed
end-to-end from here. Before relying on this script:
  1. Open the dataset page above in a normal browser.
  2. Click its "API" tab to get the current resource id ("rid") and a
     sample response -- data.taipei's dataset UUID (in the page URL) and
     the resource id used by the API are not always the same value.
  3. Update RESOURCE_ID and COLUMN_MAP below to match what you see.

Run: python fetch_mrt_hourly.py
Output: ../data/mrt_hourly.csv with columns [station, hour, entries, exits]
        summed across whatever date range the API call returns, for the
        stations returned by stations_in_radius().
"""

import csv
import sys

import requests

from stations import stations_in_radius

# TODO verify against the dataset's "API" tab (see module docstring).
RESOURCE_ID = "63f31c7e-7fc3-418b-bd82-b95158755b4d"
API_URL = f"https://data.taipei/api/v1/dataset/{RESOURCE_ID}"
PAGE_LIMIT = 1000

# Maps our internal field names to the likely source column names.
# data.taipei datasets are inconsistent about English vs. Chinese headers,
# so list every variant you find on the dataset page here.
COLUMN_MAP = {
    "station": ["站名", "進站", "station", "SNAME"],
    "hour": ["時段", "小時", "hour"],
    "entries": ["進站人數", "entries", "轉入"],
    "exits": ["出站人數", "exits", "轉出"],
}


def pick(row: dict, candidates: list[str]):
    for key in candidates:
        if key in row:
            return row[key]
    return None


def fetch_rows():
    resp = requests.get(
        API_URL,
        params={"scope": "resourceAquire", "limit": PAGE_LIMIT},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("result", {}).get("results", [])


def main():
    wanted = {s.name for s, _d in stations_in_radius()}
    if not wanted:
        print("No stations resolved within radius -- check config.py", file=sys.stderr)
        sys.exit(1)

    try:
        rows = fetch_rows()
    except requests.RequestException as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        print(
            "If this is a 403/connection error, your network may be blocking "
            "data.taipei -- this happens inside restricted sandboxes.",
            file=sys.stderr,
        )
        sys.exit(1)

    out_rows = []
    for row in rows:
        station = pick(row, COLUMN_MAP["station"])
        if station not in wanted:
            continue
        out_rows.append(
            {
                "station": station,
                "hour": pick(row, COLUMN_MAP["hour"]),
                "entries": pick(row, COLUMN_MAP["entries"]) or 0,
                "exits": pick(row, COLUMN_MAP["exits"]) or 0,
            }
        )

    if not out_rows:
        print(
            "No matching rows -- the COLUMN_MAP or RESOURCE_ID likely need "
            "updating to match the live dataset (see module docstring).",
            file=sys.stderr,
        )
        sys.exit(1)

    with open("../data/mrt_hourly.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["station", "hour", "entries", "exits"])
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} rows to ../data/mrt_hourly.csv")


if __name__ == "__main__":
    main()
