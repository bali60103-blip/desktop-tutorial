import json,math
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import Polygon,Point
root=Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');reg=json.load(open(root/'registration.json'));fit=reg['live_to_twd97'];a=math.radians(fit['rotation_degrees']);org=[reg['origin_epsg3826'][i]+fit['translation'][i] for i in range(2)];tr=Transformer.from_crs(4326,3826,always_xy=True)
def live(q):
 x,y=tr.transform(*q);x-=org[0];y-=org[1];return[(math.cos(a)*x+math.sin(a)*y)/fit['scale'],(-math.sin(a)*x+math.cos(a)*y)/fit['scale']]
p=json.load(open('/tmp/civic-y26-context/osm_context.json'));e=next(e for e in json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'))['entries'] if e['ref']=='Y26');pt=Point(e['live_xy']);b=[]
for w in p['ways']:
 if 'building' in w['tags']:
  g=Polygon([live(q) for q in w['coords']]);b.append((g.distance(pt),w,g))
dist,w,g=min(b,key=lambda v:v[0]);q=list(g.minimum_rotated_rectangle.exterior.coords);u,v=max(zip(q,q[1:]),key=lambda ab:math.dist(*ab));dx,dy=v[0]-u[0],v[1]-u[1]
if dx>0:dx,dy=-dx,-dy
new=math.atan2(dy,dx);old=math.atan2(e['lower_landing_xy'][1]-e['live_xy'][1],e['lower_landing_xy'][0]-e['live_xy'][0]);r={'anchor_live_xy':e['live_xy'],'reference_building_osm_id':w['id'],'building_distance_m':dist,'reference_building_live_xy':list(g.exterior.coords),'original_axis_degrees_from_live_x':math.degrees(old),'alternative_axis_degrees_from_live_x':math.degrees(new),'rotation_radians':new-old,'status':'Alternative inferred from nearest building long axis, westward sign chosen as hypothesis. No observed Y26 footprint or measured photograph pose. Not verified correction. OSM entrance anchor unchanged.'};Path('/tmp/civic-y26-context/orientation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False))
