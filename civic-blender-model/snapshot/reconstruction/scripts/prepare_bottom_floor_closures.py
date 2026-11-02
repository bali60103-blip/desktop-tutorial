import json,pathlib,os
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';rows=json.load(open(out/'bottom_floor_opening_inventory.json'));payload=[];unmatched=[]
for r in rows:
 vs=r['vertices'];z0=min(v[2] for v in vs);z1=max(v[2] for v in vs);g=unary_union([Polygon([vs[i][:2] for i in f]) for f in r['faces'] if all(abs(vs[i][2]-z1)<.0001 for i in f)]);parts=list(g.geoms) if hasattr(g,'geoms') else [g];holes=[Polygon(h) for p in parts for h in p.interiors];chosen=[];matches=[]
 for p in r['paths']:
  if not p['id'].endswith('_A'):continue
  q=Point((p['a'][0]+p['b'][0])/2,(p['a'][1]+p['b'][1])/2);candidates=[h for h in holes if h.area<100 and h.buffer(.03).covers(q)]
  if not candidates:unmatched.append({'floor':r['object'],'core_path':p['id'],'reason':'No enclosed stair hole found; boundary notch requires separate review'});continue
  h=min(candidates,key=lambda p:p.area);chosen.append(h);matches.append(p['id'])
 if not chosen:continue
 new=unary_union([g,*chosen]);verts=[];faces=[];lookup={}
 def idx(x,y,z):
  key=(round(x,6),round(y,6),round(z,6))
  if key not in lookup:lookup[key]=len(verts);verts.append(list(key))
  return lookup[key]
 for poly in list(new.geoms) if hasattr(new,'geoms') else [new]:
  p=orient(poly,1)
  for tri in constrained_delaunay_triangles(p).geoms:
   co=list(orient(tri,1).exterior.coords)[:-1];faces.extend([[idx(x,y,z1) for x,y in co],[idx(x,y,z0) for x,y in reversed(co)]])
  for ring in [p.exterior,*p.interiors]:
   co=list(ring.coords)
   for a,b in zip(co,co[1:]):faces.append([idx(*a,z0),idx(*b,z0),idx(*b,z1),idx(*a,z1)])
 edges={}
 for f in faces:
  for a,b in zip(f,f[1:]+f[:1]):e=tuple(sorted((a,b)));edges[e]=edges.get(e,0)+1
 assert all(n==2 for n in edges.values()),r['object']
 payload.append({'object':r['object'],'section':r['section'],'level':r['level'],'vertices':verts,'faces':faces,'area_added_m2':new.area-g.area,'closed_core_paths':matches,'z0':z0,'z1':z1})
r={'items':payload,'unmatched':unmatched,'scope':'Close only enclosed generated stair voids in the lowest modeled parking floor. No upper circulation openings or unmatched boundary notches altered.'};(out/'bottom_floor_closure_payload.json').write_text(json.dumps(r,ensure_ascii=False));print(json.dumps({'floors':len(payload),'filled_area_m2':sum(r['area_added_m2'] for r in payload),'matched_cores':sum(len(r['closed_core_paths']) for r in payload),'unmatched':unmatched},ensure_ascii=False,indent=2))
