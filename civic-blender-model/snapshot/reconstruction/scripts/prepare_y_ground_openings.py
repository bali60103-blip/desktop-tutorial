import json,runpy
from pathlib import Path
from collections import defaultdict
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
from shapely import set_precision
mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh'];root=Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'YGroundOpenings';entries=json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'))['entries'];audit=json.load(open(out/'ground_opening_audit.json'));blocked={r['ref'] for r in audit if r['ground_hits']};cuts=[];areas=[]
for e in entries:
 if e['ref'] not in blocked:continue
 x,y=e['live_xy'];ex,ey=e['lower_landing_xy'];dx,dy=ex-x,ey-y;length=(dx*dx+dy*dy)**.5;dx/=length;dy/=length
 cuts.append(LineString([(x-dx*.3,y-dy*.3),(x+dx*7.5,y+dy*7.5)]).buffer(1.4,cap_style=2));areas.append(Point(x,y).buffer(18))
cut=unary_union(cuts);area=unary_union(areas);groups=defaultdict(list)
for f in json.load(open(out/'source_ground_faces.json')):
 q=Polygon([v[:2] for v in f['vertices']])
 if q.is_valid and q.area>.0001:groups[(f['source'],round(f['vertices'][0][2],4))].append(q)
rows=[]
for (name,z),polys in groups.items():
 before=set_precision(unary_union(polys).intersection(area),.0001);after=set_precision(before.difference(cut),.0001)
 for i,g in enumerate([after] if after.geom_type=='Polygon' else getattr(after,'geoms',[])):
  if g.geom_type!='Polygon' or g.area<.001:continue
  m=mesh(g,z-.08,z);assert all(len(f)==len(set(f)) for f in m['faces']);rows.append({'name':name+'_OPENING_PATCH_'+str(z)+'_'+str(i),'mesh':m,'source':name,'top_z':z,'removed_area_group_m2':before.area-after.area})
p={'patches':rows,'entrances':sorted(blocked),'note':'Local 18m-radius patch around two blocked entries, horizontal source faces only. 0.08m patch thickness assumed; source XY/topZ retained. Holes follow estimated stairs, not measured. No new terrain for other17 entries.'};(out/'ground_patch_payload.json').write_text(json.dumps(p,ensure_ascii=False));print({'patch_meshes':len(rows),'entries':sorted(blocked)})
