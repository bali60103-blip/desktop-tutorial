import json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
p=Path('/tmp/civic-mall');rows=[]
def mesh(poly,z0,z1):
 tris=constrained_delaunay_triangles(poly);vs=[];fs=[];ids={}
 def idx(q,z):
  k=(round(q[0],7),round(q[1],7),z)
  if k not in ids:ids[k]=len(vs);vs.append(k)
  return ids[k]
 for t in tris.geoms:
  xy=list(t.exterior.coords)[:3];fs.append([idx(q,z1) for q in xy]);fs.append([idx(q,z0) for q in xy[::-1]])
 for ring in [poly.exterior,*poly.interiors]:
  xy=list(ring.coords)
  for a,b in zip(xy,xy[1:]):fs.append([idx(a,z0),idx(b,z0),idx(b,z1),idx(a,z1)])
 return {'vertices':vs,'faces':fs}
for obj in json.loads((p/'legacy.json').read_text()):
 polys=[]
 for f in obj['faces']:
  v=[obj['vertices'][i] for i in f]
  if max(q[2] for q in v)-min(q[2] for q in v)<.001:
   g=Polygon([q[:2] for q in v]);
   if g.is_valid and g.area>.01:polys.append(g)
 g=unary_union(polys)
 if g.geom_type!='Polygon':raise ValueError(obj['name'])
 parts=[{'part':'FLOOR','mesh':mesh(g,-3.9,-3.6)},{'part':'REMOVABLE_ROOF','mesh':mesh(g,-.8,-.55)}]
 wall=g.difference(g.buffer(-.2))
 for i,w in enumerate([wall] if wall.geom_type=='Polygon' else wall.geoms):parts.append({'part':'PERIMETER_WALL_'+str(i),'mesh':mesh(w,-3.6,-.8)})
 rows.append({'source':obj['name'],'footprint_area_m2':g.area,'bounds':g.bounds,'parts':parts,'status':'LEGACY XY UNREGISTERED; floor -3.6m and clear height 2.8m user-approved assumptions; wall 0.2m slab 0.3m roof 0.25m estimates; entrances and shops not inferred','identity':'STATION ENVELOPE UNCLASSIFIED, NOT IDENTIFIED Y MALL' if obj['name']=='Taipei_Station_Underground' else 'LEGACY NAMED UNDERGROUND ENVELOPE'})
(p/'payload.json').write_text(json.dumps(rows,ensure_ascii=False));print([(r['source'],round(r['footprint_area_m2'],1)) for r in rows])
