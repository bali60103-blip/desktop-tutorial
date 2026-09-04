"""Small shared GIS helpers: CRS conversion and shapefile loading."""

import json

from pyproj import Transformer

from config import CRS_PROJECTED, CRS_WGS84

_to_proj = Transformer.from_crs(CRS_WGS84, CRS_PROJECTED, always_xy=True)
_to_wgs84 = Transformer.from_crs(CRS_PROJECTED, CRS_WGS84, always_xy=True)


def wgs84_to_proj(lon, lat):
    return _to_proj.transform(lon, lat)


def proj_to_wgs84(x, y):
    return _to_wgs84.transform(x, y)


def load_geojson(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_shapefile_as_geojson(shp_path, encoding="big5"):
    """Read a .shp/.dbf pair with pyshp and return a GeoJSON-like dict.
    Coordinates are left as-is (caller must know the source CRS)."""
    import shapefile

    sf = shapefile.Reader(shp_path, encoding=encoding)
    features = []
    for sr in sf.shapeRecords():
        geom = sr.shape.__geo_interface__
        props = sr.record.as_dict()
        for k, v in list(props.items()):
            if hasattr(v, "isoformat"):
                props[k] = v.isoformat()
        features.append({"type": "Feature", "geometry": geom, "properties": props})
    return {"type": "FeatureCollection", "features": features}
