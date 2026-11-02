import json,math,re
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union,nearest_points
reg=json.load(open('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/registration.json'));fit=reg['live_to_twd97'];a=math.radians(fit['rotation_degrees']);org=[reg['origin_epsg3826'][i]+fit['translation'][i] for i in range(2)];tr=Transformer.from_crs(4326,3826,always_xy=True)
polys={}
for r in json.load(open('/tmp/civic-mall/legacy.json')):
 pp=[]
 for f in r['faces']:
  v=[r['vertices'][i] for i in f]
  if max(q[2] for q in v)-min(q[2] for q in v)<.001:
   p=Polygon([q[:2] for q in v])
   if p.is_valid and p.area>.1:pp.append(p)
 polys[r['name']]=unary_union(pp)
rows=[]
for f in json.load(open('/tmp/civic-stage01/entrance_candidates.geojson'))['features']:
 t=f['properties'];ref=t.get('ref',t.get('name',''))
 if not re.fullmatch('[RY][0-9]+',ref):continue
 x,y=tr.transform(*f['geometry']['coordinates']);x-=org[0];y-=org[1];xy=((math.cos(a)*x+math.sin(a)*y)/fit['scale'],(-math.sin(a)*x+math.cos(a)*y)/fit['scale']);p=Point(xy);name,g=min(polys.items(),key=lambda kv:kv[1].distance(p));q=nearest_points(p,g.boundary)[1]
 rows.append({'ref':ref,'osm_id':t['osm_id'],'live_xy':xy,'nearest_legacy':name,'distance_to_polygon_m':g.distance(p),'distance_to_boundary_m':g.boundary.distance(p),'nearest_boundary_xy':[q.x,q.y],'inside':g.contains(p)})
Path('/tmp/civic-mall/entries.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print(json.dumps(rows,ensure_ascii=False,indent=2))
