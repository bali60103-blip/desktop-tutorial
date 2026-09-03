"""Shared configuration for the 市民大道一段 activity-heatmap pipeline.

IMPORTANT: this project does NOT have access to real telecom/mobile-signaling
population-flow data (that data is proprietary to carriers and not published
as open data). Everything here is built from Taipei City open data (MRT
hourly ridership, YouBike station activity) used as a PROXY for pedestrian
activity, not a direct measurement of population flow. See ../data_sources.md
for full citations and caveats.
"""

from dataclasses import dataclass

# Approximate centroid of 市民大道一段 (Section 1 of Civic Boulevard),
# the stretch roughly between Huanhe N. Rd. and Zhongshan N. Rd. in
# Datong District, Taipei -- near Beimen / the north side of Taipei
# Main Station. Adjust if you have a more precise definition of the
# section's extent (e.g. exact start/end intersections).
CENTER_LAT = 25.0520
CENTER_LON = 121.5120
RADIUS_KM = 2.0


@dataclass(frozen=True)
class Station:
    name: str
    lat: float
    lon: float


# Well-known MRT station coordinates near 市民大道一段. Only stations within
# RADIUS_KM of CENTER_LAT/CENTER_LON (computed at runtime via haversine) are
# actually used -- this list intentionally includes a few borderline/outside
# stations so the radius filter has something to exclude.
MRT_STATIONS = [
    Station("台北車站", 25.0478, 121.5170),
    Station("北門", 25.0511, 121.5100),
    Station("中山", 25.0526, 121.5205),
    Station("雙連", 25.0577, 121.5202),
    Station("西門", 25.0421, 121.5079),
    Station("善導寺", 25.0456, 121.5228),
    Station("台大醫院", 25.0431, 121.5161),
    Station("大橋頭", 25.0637, 121.5112),
    Station("民權西路", 25.0653, 121.5197),
    Station("小南門", 25.0378, 121.5107),
    Station("松江南京", 25.0524, 121.5327),
    Station("忠孝新生", 25.0424, 121.5327),
    Station("圓山", 25.0713, 121.5205),
    Station("南京復興", 25.0524, 121.5433),
]
