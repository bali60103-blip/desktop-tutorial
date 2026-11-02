import pathlib,json,math,runpy
from shapely.geometry import LineString,Polygon
from shapely.ops import unary_union
from shapely import set_precision
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';parts=[];issues=[];ramps=[]
mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh']
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
for r in json.load(open(root/'ParkingSections/source/payload.json'))['sections']:
 line=LineString(r['axis_live']);cuts=[]
 for i,e in enumerate(r['entrances']):
  a=e['xy'];s=line.project(__import__('shapely').geometry.Point(a));sg=1 if s<line.length/2 else -1;b=line.interpolate(max(5,min(line.length-5,s+sg*40)));dx,dy=b.x-a[0],b.y-a[1];le=math.hypot(dx,dy);d=(dx/le,dy/le);n=(-d[1],d[0]);xy=lambda st,y:(a[0]+d[0]*st+n[0]*y,a[1]+d[1]*st+n[1]*y);vs=[];fs=[]
  for j in range(81):
   t=j/80;st=le*t;g=-3.6/(le-3);z=g*st*st/6 if st<3 else (-3.6-g*(le-st)**2/6 if st>le-3 else g*(st-1.5));vs.extend([(*xy(st,-1.75),z-.25),(*xy(st,1.75),z-.25),(*xy(st,1.75),z),(*xy(st,-1.75),z)])
  for j in range(80):
   k=j*4;h=k+4;fs.extend([(k,h,h+1,k+1),(k+1,h+1,h+2,k+2),(k+2,h+2,h+3,k+3),(k+3,h+3,h,k)])
  fs.extend([(3,2,1,0),tuple(range(len(vs)-4,len(vs)))]);name='COMP_ACCESS_'+r['name']+'_'+str(i);status='ESTIMATED ground-to-B1 access; OSM candidate association/direction unverified; source ground excavation pending';parts.append({'name':name,'mesh':{'vertices':vs,'faces':fs},'status':status})
  for side in [-1,1]:
   # Two sloping retaining walls to ground, preserving ramp clear width.
   coords=[xy(0,side*1.75),xy(le,side*1.75),xy(le,side*1.95),xy(0,side*1.95)];v=[(*q,z) for q,z in zip(coords,[-.25,-3.85,-3.85,-.25])]+[(*q,.9) for q in coords];parts.append({'name':name+'_WALL_'+str(side),'mesh':{'vertices':v,'faces':faces},'status':status})
  cuts.append(Polygon([xy(-.3,-2.1),xy(le+.3,-2.1),xy(le+.3,2.1),xy(-.3,2.1)]));ramps.append({'name':name,'start':[a[0],a[1],0],'end':[b.x,b.y,-3.6],'run_m':le,'section':r['name']});issues.append({'id':name,'xy':a,'type':'access_direction_and_ground_excavation_pending','osm_id':e['osm_id']})
 # Replace completion roof only, retain stair core openings already generated.
 for part in json.load(open(out/'payload.json'))['parts']:
  if part['name']=='COMP_'+r['name']+'_ROOF':
   m=part['mesh'];top=[]
   for f in m['faces']:
    vv=[m['vertices'][i] for i in f]
    if all(abs(v[2])<.0001 for v in vv):top.append(Polygon([v[:2] for v in vv]))
   roof=set_precision(unary_union(top).difference(unary_union(cuts)),.0001)
   for j,q in enumerate([roof] if roof.geom_type=='Polygon' else roof.geoms):
    if q.geom_type=='Polygon' and q.area>.001:parts.append({'name':'COMP_ROOF_ACCESS_'+r['name']+'_'+str(j),'mesh':mesh(q,-.3,0),'status':'Estimated roof with assumed ramp and stair openings','replaces':part['name']})
p={'parts':parts,'ramps':ramps,'issues':issues};(out/'access_payload.json').write_text(json.dumps(p,ensure_ascii=False));print({'ramps':len(ramps),'parts':len(parts)})
