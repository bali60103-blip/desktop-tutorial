import os
import json,pathlib
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
out=pathlib.Path(os.environ.get('CIVIC_AUDIT_DIR','underbridge_work'));r=json.load(open(out/'linsen_median_mesh.json'));vs=r['v'];foot=unary_union([Polygon([vs[i][:2] for i in f]) for f in r['f'] if all(vs[i][2]>.17 for i in f)])
# East island head only. Keep existing model openings, further protect access envelopes.
work=foot.intersection(box(1423,690,1455,740));inv=json.load(open(pathlib.Path(os.environ.get('CIVIC_AUDIT_DIR','underbridge_work'))/'scene_inventory.json'));holes=[]
for o in inv['objects']:
 if any(t in o['name'] for t in ['RAIL_CORE_林金_0','COMP_林金_CORE0']):holes.append(box(o['lo'][0],o['lo'][1],o['hi'][0],o['hi'][1]).buffer(1.5))
if holes:work=work.difference(unary_union(holes))
curb=work.difference(work.buffer(-.15));green=work.buffer(-.3).difference(work.buffer(-1.05));pieces=[]
def extrude(poly,lo,hi):
 poly=orient(poly,1);vs=[];fs=[];ind={}
 def v(p,z):
  k=(round(p[0],5),round(p[1],5),z)
  if k not in ind:ind[k]=len(vs);vs.append(k)
  return ind[k]
 for t in constrained_delaunay_triangles(poly).geoms:
  co=list(orient(t,1).exterior.coords)[:-1];fs.append([v(p,hi) for p in co]);fs.append([v(p,lo) for p in co[::-1]])
 for ring in [poly.exterior,*poly.interiors]:
  co=list(ring.coords)
  for a,b in zip(co,co[1:]):fs.append([v(a,lo),v(b,lo),v(b,hi),v(a,hi)])
 return {'v':vs,'f':fs}
for label,geom,lo,hi in [('CURB',curb,.18,.32),('SHRUB',green,.32,.87)]:
 for i,p in enumerate(getattr(geom,'geoms',[geom])):
  if p.area>.01:pieces.append({'name':'UB_LINSEN_'+label+'_%02d_EST'%i,'kind':label,'mesh':extrude(p,lo,hi)})
(out/'linsen_mass_payload.json').write_text(json.dumps({'pieces':pieces,'footprint_source':'Existing estimated median and entrance clearances, NOT surveyed','evidence':'East Linsen island planter/shrub masses visible in 2026 user panorama; size and exact outline remain estimated','protected_access_envelopes':len(holes),'bounds':list(work.bounds)}));print({'parts':len(pieces),'bounds':work.bounds,'area':work.area})
