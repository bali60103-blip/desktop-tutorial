"""Clip generated parking paint to existing slab top polygons, preserving openings."""
import json,os,pathlib
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';r=json.load(open(out/'parking_marking_support_inventory.json'))
def top(o):
 v=o['vertices'];z=max(p[2] for p in v)
 return unary_union([Polygon([v[i][:2] for i in f]) for f in o['faces'] if all(abs(v[i][2]-z)<.0001 for i in f)])
floors={n:top(o) for n,o in r['floors'].items()};items=[]
for row in r['markings']:
 o=row['marking'];g=top(o);new=g.intersection(floors[row['floor']]);removed=g.area-new.area
 if removed<.0001:continue
 z0=min(v[2] for v in o['vertices']);z1=max(v[2] for v in o['vertices']);vs=[];fs=[];lookup={}
 def idx(x,y,z):
  k=(round(x,6),round(y,6),round(z,6))
  if k not in lookup:lookup[k]=len(vs);vs.append(list(k))
  return lookup[k]
 for p in list(new.geoms) if hasattr(new,'geoms') else [new]:
  if p.is_empty or p.geom_type!='Polygon' or p.area<.000001:continue
  p=orient(p,1)
  for tri in constrained_delaunay_triangles(p).geoms:
   co=list(orient(tri,1).exterior.coords)[:-1];fs.extend([[idx(x,y,z1) for x,y in co],[idx(x,y,z0) for x,y in reversed(co)]])
  for ring in [p.exterior,*p.interiors]:
   for a,b in zip(list(ring.coords),list(ring.coords)[1:]):fs.append([idx(*a,z0),idx(*b,z0),idx(*b,z1),idx(*a,z1)])
 items.append({'object':o['name'],'floor':row['floor'],'removed_area_m2':removed,'vertices':vs,'faces':fs,'source_vertices':o['vertices']})
(out/'supported_parking_markings_payload.json').write_text(json.dumps({'checked':len(r['markings']),'items':items},ensure_ascii=False));print(json.dumps({'checked':len(r['markings']),'changed':len(items),'removed_m2':sum(x['removed_area_m2'] for x in items)},ensure_ascii=False))
