import json,os,pathlib,math
from shapely.geometry import Polygon,Point
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
from shapely.ops import unary_union,triangulate
from shapely.affinity import translate
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';rows=json.load(open(out/'gongzhong_integration_surfaces.json'));case=json.load(open(out/'core_integration_search.json'))['cases'][0];delta=case['chosen']['translation']
def top_poly(r):
 vs=r['vertices'];z=max(v[2] for v in vs);return unary_union([Polygon([vs[i][:2] for i in f]) for f in r['faces'] if all(abs(vs[i][2]-z)<1e-4 for i in f)])
g=top_poly(next(r for r in rows if r['name']=='COMP_公中_B1_FLOOR'));oldhole=min((Polygon(h) for h in g.interiors),key=lambda h:h.distance(Point(870.9,785.7)));assert 18<oldhole.area<20;newhole=translate(oldhole,xoff=delta[0],yoff=delta[1]);payload=[];skips=[]
for r in rows:
 if len(r['z_levels'])!=2:skips.append({'name':r['name'],'reason':'Non-flat source retained; must check in full assembly'});continue
 source=top_poly(r);oldarea=source.area;own=r['name'] in ['COMP_公中_B1_FLOOR','COMP_公中_B2_FLOOR','COMP_ROOF_ACCESS_公中_0'];filled=source.union(oldhole) if own else source;remain=filled.difference(newhole)
 if source.symmetric_difference(remain).area<1e-5:continue
 z0,z1=r['z_levels'];vs=[];fs=[];lookup={}
 def idx(x,y,z):
  k=(round(x,6),round(y,6),round(z,6))
  if k not in lookup:lookup[k]=len(vs);vs.append(list(k))
  return lookup[k]
 gs=list(remain.geoms) if hasattr(remain,'geoms') else [remain]
 for p in gs:
  if p.is_empty or p.area<1e-8:continue
  p=orient(p,sign=1)
  for tri in constrained_delaunay_triangles(p).geoms:
   if not p.covers(tri):continue
   co=list(tri.exterior.coords)[:-1];fs.extend([[idx(x,y,z1) for x,y in co],[idx(x,y,z0) for x,y in reversed(co)]])
  for ring in [p.exterior,*p.interiors]:
   co=list(ring.coords)
   for a,b in zip(co,co[1:]):fs.append([idx(*a,z0),idx(*b,z0),idx(*b,z1),idx(*a,z1)])
 edges={}
 for f in fs:
  for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
 assert all(n==2 for n in edges.values()),r['name']
 payload.append({'source':r['name'],'vertices':vs,'faces':fs,'old_area_m2':oldarea,'new_area_m2':remain.area,'old_core_hole_filled':own,'new_hole_overlap_removed_m2':filled.intersection(newhole).area})
report={'translation':delta,'status':'Unadopted integrated estimate; original working scene preserved','old_hole_xy':list(oldhole.exterior.coords),'new_hole_xy':list(newhole.exterior.coords),'items':payload,'skips':skips};(out/'gongzhong_integrated_openings_payload.json').write_text(json.dumps(report));print(json.dumps({**{k:v for k,v in report.items() if k not in ['items','old_hole_xy','new_hole_xy']},'items':[{k:v for k,v in r.items() if k not in ['vertices','faces']} for r in payload]},ensure_ascii=False,indent=2))
