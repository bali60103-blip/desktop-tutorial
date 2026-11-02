import os,pathlib,json
from shapely.geometry import Polygon
from shapely.ops import unary_union,triangulate
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';rows=json.load(open(out/'parking_horizontal_faces.json'));payload=[]
for name in ['B2_SLAB','B1_SLAB_west','B1_SLAB_east','B1_SLAB_north','B1_SLAB_south']:
 own=[r for r in rows if r['object']==name];z0=min(r['z'] for r in own);z1=max(r['z'] for r in own);top=unary_union([Polygon(r['xy']) for r in own if abs(r['z']-z1)<.001]);target='COMP_\u4e2d\u6797_'+('B2' if name=='B2_SLAB' else 'B1')+'_FLOOR';new=unary_union([Polygon(r['xy']) for r in rows if r['object']==target and abs(r['z']-z1)<.001]);remain=top.difference(new);geoms=list(remain.geoms) if hasattr(remain,'geoms') else [remain];vs=[];fs=[];lookup={}
 def idx(x,y,z):
  k=(round(x,6),round(y,6),round(z,6))
  if k not in lookup:lookup[k]=len(vs);vs.append(list(k))
  return lookup[k]
 for poly in geoms:
  if poly.is_empty or poly.area<1e-8:continue
  for tri in triangulate(poly):
   if not poly.covers(tri):continue
   co=list(tri.exterior.coords)[:-1];a=[idx(x,y,z0) for x,y in co];b=[idx(x,y,z1) for x,y in co];fs.extend([list(reversed(a)),b])
  for ring in [poly.exterior,*poly.interiors]:
   co=list(ring.coords)
   for a,b in zip(co,co[1:]):fs.append([idx(*a,z0),idx(*b,z0),idx(*b,z1),idx(*a,z1)])
 counts={}
 for f in fs:
  for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted([a,b]));counts[k]=counts.get(k,0)+1
 assert all(v==2 for v in counts.values()),name
 payload.append({'source':name,'target':target,'vertices':vs,'faces':fs,'original_area_m2':top.area,'removed_area_m2':top.intersection(new).area,'retained_area_m2':remain.area,'z0':z0,'z1':z1,'scope':'Remove exact plan overlap with working replacement floor, preserve unoverlapped legacy fragments; not a survey correction'})
(out/'legacy_slab_trim_payload.json').write_text(json.dumps(payload));print(json.dumps([{k:v for k,v in p.items() if k not in ['vertices','faces']} for p in payload],indent=2))
