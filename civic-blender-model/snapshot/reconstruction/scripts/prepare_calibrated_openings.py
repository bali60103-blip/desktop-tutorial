import json,pathlib,runpy,math
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
from shapely import make_valid,set_precision
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Calibration';mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh'];cuts=[];records=[]
def cut(name,g,source):cuts.append(g);records.append({'id':name,'geometry':g.__geo_interface__,'source':source,'status':'Opening follows current working access geometry, not surveyed excavation'})
for r in json.load(open(root/'CompletionPass/access_payload.json'))['ramps']:cut(r['name'],LineString([r['start'][:2],r['end'][:2]]).buffer(2.1,cap_style=2),'OSM or assumed parking entrance, direction still provisional')
for r in json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'))['entries']:
 if not r['built']:continue
 a=r['live_xy'];b=r['lower_landing_xy'];d=math.dist(a,b);u=[(b[i]-a[i])/d for i in [0,1]];cut('Y_'+r['ref'],LineString([[a[i]-.3*u[i] for i in [0,1]],[a[i]+7.5*u[i] for i in [0,1]]]).buffer(1.4,cap_style=2),'Mapped Y entrance point; stair direction estimated')
# Match explicit cores in completion source, including landing width.
for r in json.load(open(root/'ParkingSections/source/payload.json'))['sections']:
 line=LineString(r['axis_live']);a=line.coords[0];b=line.coords[-1];L=line.length;d=((b[0]-a[0])/L,(b[1]-a[1])/L);n=(-d[1],d[0])
 for i,s in enumerate([10,L-14]):
  g=Polygon([(a[0]+d[0]*x+n[0]*y,a[1]+d[1]*x+n[1]*y) for x,y in [(s-.1,6.9),(s+4.8,6.9),(s+4.8,11.1),(s-.1,11.1)]]);cut('CORE_'+r['name']+'_'+str(i),g,'Generic estimated parking stair core')
# R1 raw step footprint.
r1=[]
for r in json.load(open(root/'CompletionPass/malls_payload.json'))['parts']:
 if r['name'].startswith('COMP_R1_STEP'):
  vs=r['mesh']['vertices'];r1.append(Polygon([v[:2] for v in vs]).convex_hull)
if r1:cut('R1',unary_union(r1).buffer(.2),'Mapped R1 point; heading estimated')
opening=set_precision(unary_union(cuts),.001);parts=[];reports=[]
for r in json.load(open(out/'evaluated_ground.json')):
 top=max(v[2] for v in r['vertices']);bottom=min(v[2] for v in r['vertices']);ps=[]
 for f in r['faces']:
  vv=[r['vertices'][i] for i in f]
  if all(abs(v[2]-top)<1e-6 for v in vv):
   p=Polygon([v[:2] for v in vv])
   if p.is_valid and p.area>1e-8:ps.append(p)
 old=set_precision(unary_union(ps),.001);g=set_precision(make_valid(old.difference(opening)),.001);afterparts=[]
 for i,p in enumerate([g] if g.geom_type=='Polygon' else g.geoms):
  if p.geom_type=='Polygon' and p.area>.001:
   name='CAL_'+r['name']+'_'+str(i);parts.append({'name':name,'replaces':r['name'],'mesh':mesh(p,bottom,top),'status':'Existing XY/elevation preserved outside current access cuts; excavation footprint is provisional'});afterparts.append(name)
 reports.append({'source_object':r['name'],'before_area_m2':old.area,'after_area_m2':g.area,'cut_area_m2':old.area-g.area,'preserved_z':[bottom,top],'new_objects':afterparts})
(out/'openings_payload.json').write_text(json.dumps({'parts':parts,'reports':reports,'openings':records},ensure_ascii=False));print({'parts':len(parts),'openings':len(records),'cut_areas':[(r['source_object'],r['cut_area_m2']) for r in reports]})
