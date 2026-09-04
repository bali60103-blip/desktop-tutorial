"""Load the site boundary and clip feature collections against it.

All the raw datasets are in EPSG:3826 (TWD97 TM) already, which is convenient
because the site boundary buffer was also built in meters in that CRS. So
clipping is done directly in EPSG:3826 — no reprojection needed per feature.
"""

import json
import os

from shapely.geometry import shape
from shapely.prepared import prep

from config import PROCESSED_DIR
from gis_utils import wgs84_to_proj

_boundary_3826 = None


def site_boundary_3826():
    global _boundary_3826
    if _boundary_3826 is None:
        with open(os.path.join(PROCESSED_DIR, "site_boundary.geojson"), encoding="utf-8") as f:
            d = json.load(f)
        geom_wgs84 = shape(d["features"][0]["geometry"])
        # reproject boundary polygon ring by ring
        from shapely.ops import transform

        _boundary_3826 = transform(lambda lon, lat: wgs84_to_proj(lon, lat), geom_wgs84)
    return _boundary_3826


def clip_features_3826(features, geom_key="geometry"):
    """features: list of GeoJSON Feature dicts whose geometry is already in
    EPSG:3826 coordinates. Returns the subset whose geometry intersects the
    site boundary."""
    boundary = prep(site_boundary_3826())
    kept = []
    for feat in features:
        geom = feat.get(geom_key)
        if not geom:
            continue
        try:
            g = shape(geom)
        except Exception:
            continue
        if g.is_empty:
            continue
        if boundary.intersects(g):
            kept.append(feat)
    return kept


def clip_points_xy(records, x_key, y_key):
    """records: list of dicts with numeric x/y fields in EPSG:3826.
    Returns the subset inside the site boundary."""
    from shapely.geometry import Point

    boundary = prep(site_boundary_3826())
    kept = []
    for r in records:
        x, y = r.get(x_key), r.get(y_key)
        if x is None or y is None:
            continue
        try:
            x, y = float(x), float(y)
        except (TypeError, ValueError):
            continue
        if boundary.contains(Point(x, y)):
            kept.append(r)
    return kept
