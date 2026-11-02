import json,math,runpy
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
root=Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Y26Orientation';raw=json.load(open(root/'UndergroundShells/source/legacy.json'));r=next(r for r in raw if r['name']=='Taipei_Station_Underground')
def footprint(vs,fs):
 ps=[]
 for f in fs:
  v=[vs[i] for i in f]
  if max(q[2] for q in v)-min(q[2] for q in v)<.0001:
   p=Polygon([q[:2] for q in v])
   if p.is_valid and p.area>.0001:ps.append(p)
 return unary_union(ps)
g=footprint(r['vertices'],r['faces']);b=next(r for r in json.load(open(out/'connection_payload.json')) if r['variant']=='B');m=b['parts'][0]['mesh'];conn=footprint(m['vertices'],m['faces']);full=set_precision(unary_union([g,conn]),.0001)
p=json.load(open(out/'orientation.json'));ang=math.radians(p['alternative_axis_degrees_from_live_x']);a=p['anchor_live_xy'];d=(math.cos(ang),math.sin(ang));n=(-d[1],d[0])
def xy(x,y):return(a[0]+d[0]*x+n[0]*y,a[1]+d[1]*x+n[1]*y)
mouth=LineString([xy(8.4,-2.65),xy(8.4,2.65)]).buffer(.35);walls=set_precision(full.difference(full.buffer(-.2)).difference(mouth),.0001);mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh'];parts=[{'name':'Y26_B_INTEGRATED_FLOOR','mesh':mesh(full,-3.9,-3.6)}]
for i,q in enumerate([walls] if walls.geom_type=='Polygon' else walls.geoms):
 if q.geom_type=='Polygon' and q.area>.0001:parts.append({'name':'Y26_B_INTEGRATED_WALL_'+str(i),'mesh':mesh(q,-3.6,-.8)})
start=Point(xy(9.15,0));edge=nearest_points(start,g.boundary)[1];dx,dy=edge.x-start.x,edge.y-start.y;le=math.hypot(dx,dy);end=(edge.x+dx/le*1.5,edge.y+dy/le*1.5);path=[xy(8.4,-1),xy(9.15,-1),xy(9.15,0),end];line=LineString(path)
assert full.buffer(.001).covers(line);assert walls.intersection(line).length<.001
assert all(len(f)==len(set(f)) for p in parts for f in p['mesh']['faces'])
r={'parts':parts,'walk_path_xy':path,'floor_connected':full.geom_type=='Polygon','wall_centerline_intersection_m':walls.intersection(line).length,'status':'Integrated B alternative only; legacy shell XY and entrance orientation/dimensions remain estimates. Centerline is not a full-body clearance or egress check.'};(out/'integrated_payload.json').write_text(json.dumps(r));print({k:v for k,v in r.items() if k!='parts'})
