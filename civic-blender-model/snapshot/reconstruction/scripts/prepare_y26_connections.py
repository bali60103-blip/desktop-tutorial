import json,math,runpy
from pathlib import Path
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
root=Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Y26Orientation';p=json.load(open(out/'orientation.json'));legacy=json.load(open(root/'UndergroundShells/source/legacy.json'));r=next(r for r in legacy if r['name']=='Taipei_Station_Underground');polys=[]
for f in r['faces']:
 v=[r['vertices'][i] for i in f]
 if max(x[2] for x in v)-min(x[2] for x in v)<.001:
  g=Polygon([x[:2] for x in v])
  if g.is_valid and g.area>.1:polys.append(g)
g=unary_union(polys);mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh'];rows=[]
for label,key in [('A','original_axis_degrees_from_live_x'),('B','alternative_axis_degrees_from_live_x')]:
 a=p['anchor_live_xy'];t=math.radians(p[key]);d=(math.cos(t),math.sin(t));n=(-d[1],d[0])
 def xy(x,y):return(a[0]+d[0]*x+n[0]*y,a[1]+d[1]*x+n[1]*y)
 landing=Polygon([xy(8.4,-2.5),xy(9.9,-2.5),xy(9.9,2.5),xy(8.4,2.5)]);start=Point(xy(9.15,0));b=nearest_points(start,g.boundary)[1];dx,dy=b.x-start.x,b.y-start.y;l=math.hypot(dx,dy)
 if g.contains(start):end=start;line=LineString([xy(8.4,0),xy(9.9,0)])
 else:
  end=Point(b.x+dx/l*1.5,b.y+dy/l*1.5);line=LineString([start,end]);assert g.contains(end)
 floor=set_precision(unary_union([landing,line.buffer(1.2,cap_style=2)]),.0001);walls=set_precision(floor.difference(floor.buffer(-.15)),.0001)
 # Remove wall across stairs/escalator mouths and final connection to mall.
 mouth=LineString([xy(8.4,-2.6),xy(8.4,2.6)]).buffer(.3);wall=walls.difference(mouth).difference(g.buffer(.05));wall=set_precision(wall,.0001)
 parts=[{'name':label+'_LOWER_LANDING_CONNECTION','mesh':mesh(floor,-3.9,-3.6)}]
 for i,q in enumerate([wall] if wall.geom_type=='Polygon' else wall.geoms):
  if q.geom_type=='Polygon' and q.area>.001:parts.append({'name':label+'_CONNECTION_WALL_'+str(i),'mesh':mesh(q,-3.6,-.8)})
 assert all(len(f)==len(set(f)) for m in parts for f in m['mesh']['faces'])
 rows.append({'variant':label,'parts':parts,'gap_to_legacy_floor_m':start.distance(g),'landing_inside_legacy':g.contains(start),'endpoint_inside_legacy':g.contains(end),'status':'ASSUMED local landing and shortest connector to legacy shell; routing not confirmed by survey or official plan. Existing shell wall opening still requires integration.'})
(out/'connection_payload.json').write_text(json.dumps(rows));print([{k:v for k,v in r.items() if k!='parts'} for r in rows])
