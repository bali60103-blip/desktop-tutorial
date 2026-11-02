import json,pathlib,os
from shapely.geometry import Polygon,Point,LineString
from shapely import set_precision
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';rows=json.load(open(out/'bottom_floor_opening_inventory.json'));payload=[];unmatched=[];sections={r['name']:r for r in json.load(open(out.parent/'ParkingSections/source/payload.json'))['sections']};pending=json.load(open(out/'bottom_floor_closure_report.json'))['unmatched']
for r in rows:
 vs=r['vertices'];z0=min(v[2] for v in vs);z1=max(v[2] for v in vs);g=unary_union([Polygon([vs[i][:2] for i in f]) for f in r['faces'] if all(abs(vs[i][2]-z1)<.0001 for i in f)]);chosen=[];matches=[]
 section=sections[r['section']];line=LineString(section['axis_live']);L=line.length;a=line.coords[0];b=line.coords[-1];d=((b[0]-a[0])/L,(b[1]-a[1])/L);n=(-d[1],d[0]);outline=set_precision(Polygon(section['outline']),.001)
 for item in pending:
  if item['floor']!=r['object']:continue
  core=int(item['core_path'].split('_')[2]);start=10 if core==0 else L-14
  hole=Polygon([(a[0]+d[0]*x+n[0]*y,a[1]+d[1]*x+n[1]*y) for x,y in [(start,7),(start+4.7,7),(start+4.7,11),(start,11)]])
  chosen.append(set_precision(hole.buffer(.002).intersection(outline),.001));matches.append(item['core_path'])
 g=set_precision(g,.001)
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
r={'items':payload,'unmatched':unmatched,'scope':'Restore generated stair boundary notches within the original estimated parking outline only. Original generator rectangles recovered; coordinates snapped within1mm. No footprint expansion or stair movement.'};(out/'bottom_notch_closure_payload.json').write_text(json.dumps(r,ensure_ascii=False));print(json.dumps({'floors':len(payload),'filled_area_m2':sum(r['area_added_m2'] for r in payload),'matched_cores':sum(len(r['closed_core_paths']) for r in payload),'unmatched':unmatched},ensure_ascii=False,indent=2))
