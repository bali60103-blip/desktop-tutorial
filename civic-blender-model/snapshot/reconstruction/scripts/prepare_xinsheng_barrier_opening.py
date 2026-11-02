import os,json,pathlib
from shapely.geometry import Polygon,shape
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'PriorityNodes_20260914'
s=json.load(open(out/'xinsheng_barrier_source.json'));r=json.load(open(out/'xinsheng_ramp_payload.json'))
v=s['vertices'];tops=[Polygon([v[i][:2] for i in f]) for f in s['faces'] if all(v[i][2]>9 for i in f)]
old=unary_union(tops)
# Only the near-level connection area may cut the existing mainline barrier.
areas=[]
for p in r['pieces']:
 if p['material']!='ROAD':continue
 vs=p['mesh']['vertices']
 if min(v[2] for v in vs)<7.49:continue
 areas.extend(Polygon([vs[i][:2] for i in f]) for f in p['mesh']['faces'] if len(f)==3 and all(vs[i][2]>7.9 for i in f))
opening=unary_union(areas).buffer(.25)
new=old.difference(opening);parts=[]
for poly in getattr(new,'geoms',[new]):
 if poly.area<1e-6:continue
 poly=orient(poly,1);verts=[];faces=[];lookup={}
 def vi(p,z):
  key=(round(p[0],5),round(p[1],5),z)
  if key not in lookup:lookup[key]=len(verts);verts.append(key)
  return lookup[key]
 for tri in constrained_delaunay_triangles(poly).geoms:
  co=list(orient(tri,1).exterior.coords)[:-1]
  faces.append([vi(p,9.1) for p in co]);faces.append([vi(p,8) for p in reversed(co)])
 for ring in [poly.exterior,*poly.interiors]:
  for a,b in zip(list(ring.coords),list(ring.coords)[1:]):faces.append([vi(a,8),vi(b,8),vi(b,9.1),vi(a,9.1)])
 parts.append({'vertices':verts,'faces':faces})
result={'parts':parts,'old_area':old.area,'new_area':new.area,'removed_area':old.area-new.area,'opening_bounds':list(opening.bounds),'assumption':'0.25m connection clearance, near-level deck only; comparison'}
assert 0<result['removed_area']<20
(out/'xinsheng_barrier_opening_payload.json').write_text(json.dumps(result));print({k:v for k,v in result.items() if k!='parts'})
