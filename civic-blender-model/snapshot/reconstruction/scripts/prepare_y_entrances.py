"""Estimated straight stair/branch comparison tied to OSM Y entrance points. Not as-built."""
import json,runpy,math
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely import set_precision
from shapely.ops import unary_union,nearest_points
helpers=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py');mesh=helpers['mesh'];root=Path('/tmp/civic-mall');original=next(x for x in json.load(open(root/'legacy.json')) if x['name']=='Taipei_Station_Underground');polys=[]
for f in original['faces']:
 v=[original['vertices'][i] for i in f]
 if max(q[2] for q in v)-min(q[2] for q in v)<.001:
  g=Polygon([q[:2] for q in v])
  if g.is_valid and g.area>.1:polys.append(g)
g=unary_union(polys);parts=[];entries=[];cuts=[];branches=[]
for r in json.load(open(root/'entries.json')):
 if not r['ref'].startswith('Y'):continue
 p=Point(r['live_xy']);b=Point(r['nearest_boundary_xy']);dx=p.x-b.x;dy=p.y-b.y;d=math.hypot(dx,dy)
 if not g.contains(p):dx=-dx;dy=-dy
 dx/=d;dy/=d
 def point(s):return (p.x+dx*s,p.y+dy*s)
 # Straight flight toward footprint; branch length extends only if required by mapped entrance offset.
 lower=Point(point(7.2));end=Point(point(max(9, d+2 if not g.contains(p) else 9)))
 if not g.buffer(-.3).contains(end):
  entries.append({**r,'built':False,'reason':'Straight estimate cannot land within legacy floor; retained for review'});continue
 flight=LineString([point(0),point(7.2)]).buffer(1.2,cap_style=2);corr=LineString([point(7.2),end.coords[0]]).buffer(1.2,cap_style=2);cuts.append(unary_union([flight,corr]).buffer(.15));branches.append(corr)
 for i in range(24):
  a=point(i*.3);b0=point((i+1)*.3);nx=-dy*1.2;ny=dx*1.2;poly=Polygon([(a[0]+nx,a[1]+ny),(b0[0]+nx,b0[1]+ny),(b0[0]-nx,b0[1]-ny),(a[0]-nx,a[1]-ny)])
  top=-.15*i;parts.append({'name':r['ref']+'_STEP_'+str(i+1),'kind':'stairs','mesh':mesh(poly,-3.9,top)})
 entries.append({**r,'built':True,'lower_landing_xy':list(end.coords[0]),'flight_run_m':7.2,'width_m':2.4,'riser_m':.15,'tread_m':.3,'note':'Straight stair direction from nearest footprint edge, not measured. Last drop 0.15m to floor; landing and branch assumed.'})
full=unary_union([g,*branches]);opening=unary_union(cuts);walls=full.difference(full.buffer(-.2)).difference(opening)
def addpieces(name,kind,poly,z0,z1):
 poly=set_precision(poly,0.0001)
 for i,q in enumerate([poly] if poly.geom_type=='Polygon' else poly.geoms):
  if q.area>.0001:parts.append({'name':name+'_'+str(i),'kind':kind,'mesh':mesh(q,z0,z1)})
addpieces('Y_WORKING_FLOOR','floor',full,-3.9,-3.6);addpieces('Y_WORKING_WALL','wall',walls,-3.6,-.8);addpieces('Y_REMOVABLE_ROOF','roof',full.difference(opening),-.8,-.55)
r={'parts':parts,'entries':entries,'assumptions':'Legacy shell identified as candidate Y mall by proximity to19 OSM Y entrances. 2.4m-wide straight stairs are alternatives only, not verified directions or entrance types. No escalator/elevator geometry claimed. Z=0 ground assumed. Main originals preserved.','official_plan':'https://www-ws.gov.taipei/001/Upload/407/relfile/20232/9043781/822c8ec1-ad05-4acb-a5ed-b30ca11cc2f4.pdf'}
(root/'y_entrance_payload.json').write_text(json.dumps(r,ensure_ascii=False));print(json.dumps({'built':[x['ref'] for x in entries if x['built']],'unresolved':[x['ref'] for x in entries if not x['built']],'meshes':len(parts)}))
