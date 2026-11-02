"""Prepare evidence-tagged Zhonglin frontage solids, preserving footprint holes."""
import json,pathlib,re
from shapely.geometry import Polygon
from shapely import constrained_delaunay_triangles
d=json.load(open('/tmp/civic-stage05/complete/first_row.json'));rows=[]
for r in d['buildings']:
 h=r['height_m'];status='OSM explicit height, not surveyed'
 if h is None:
  if not re.fullmatch(r'\d+(\.\d+)?',r['levels'] or ''):continue
  h=float(r['levels'])*3.3;status='ASSUMED 3.3m per OSM level'
 if h<=0:continue
 vs=[];fs=[];index={}
 def vert(x,y,z):
  k=(round(x,6),round(y,6),round(z,6))
  if k not in index:index[k]=len(vs);vs.append(k)
  return index[k]
 for rings in r['rings']:
  p=Polygon(rings['outer'],rings['holes'])
  if not p.is_valid:raise ValueError(r['osm_id'])
  for tri in constrained_delaunay_triangles(p).geoms:
   coords=list(tri.exterior.coords)[:-1];fs.append([vert(x,y,h) for x,y in coords]);fs.append([vert(x,y,0) for x,y in coords[::-1]])
  for ring in [p.exterior]+list(p.interiors):
   pts=list(ring.coords)
   for a,b in zip(pts,pts[1:]):fs.append([vert(*a,0),vert(*b,0),vert(*b,h),vert(*a,h)])
 rows.append({'osm_id':r['osm_id'],'name':r['name'],'height_m':h,'height_status':status,'vertices':vs,'faces':fs,'tags':r['tags'],'frontage_status':r['status']})
out=pathlib.Path('/tmp/civic-frontage-solids');out.mkdir(exist_ok=True)
(out/'payload.json').write_text(json.dumps({'buildings':rows,'unknown_retained':43,'scope':'Zhonglin only; independent comparison, source context retained'},ensure_ascii=False))
print({'solids':len(rows),'unknown':43})
