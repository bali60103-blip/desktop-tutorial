import json,pathlib,math
from shapely.geometry import Polygon,LineString,shape,MultiPoint
from shapely.ops import unary_union
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Calibration';rows=json.load(open(out/'flow_meshes.json'));paths=[]
for r in json.load(open(root/'CompletionPass/access_payload.json'))['ramps']:paths.append({'id':r['name'],'a':r['start'],'b':r['end'],'halfwidth':1.1,'height':2.1,'mode':'vehicle envelope sample, not statutory swept-path test'})
for r in json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'))['entries']:
 if r['built']:paths.append({'id':'Y_'+r['ref'],'a':r['live_xy']+[0],'b':r['lower_landing_xy']+[-3.6],'halfwidth':.5,'height':2,'mode':'pedestrian envelope sample'})
# All generated parking cores, including both flights and landing on each floor.
for r in json.load(open(root/'ParkingSections/source/payload.json'))['sections']:
 line=LineString(r['axis_live']);a=line.coords[0];b=line.coords[-1];L=line.length;d=((b[0]-a[0])/L,(b[1]-a[1])/L);n=(-d[1],d[0])
 def pt(x,y,z):return [a[0]+d[0]*x+n[0]*y,a[1]+d[1]*x+n[1]*y,z]
 for ci,ss in enumerate([10,L-14]):
  for lev in range(1,r['levels']+1):
   z=-3.6*lev
   for flight,aa,bb in [('A',pt(ss,7.7,z+3.6),pt(ss+3.3,7.7,z+1.95)),('LANDING',pt(ss+3.9,7.7,z+1.8),pt(ss+3.9,10.1,z+1.8)),('B',pt(ss+3.3,10.1,z+1.8),pt(ss,10.1,z+.15))]:paths.append({'id':'CORE_'+r['name']+'_'+str(ci)+'_B'+str(lev)+'_'+flight,'a':aa,'b':bb,'halfwidth':.45,'height':2,'mode':'Generated stair flight envelope sample'})
# R1 tread-center route from modeled end treads.
r1=[r for r in json.load(open(root/'CompletionPass/malls_payload.json'))['parts'] if r['name'].startswith('COMP_R1_STEP')]
if r1:
 def center(r):
  vs=r['mesh']['vertices'];return [sum(v[i] for v in vs)/len(vs) for i in [0,1]]+[max(v[2] for v in vs)]
 seq=sorted([center(r) for r in r1],key=lambda a:-a[2]);paths.append({'id':'R1_TREAD_ROUTE','a':seq[0],'b':seq[-1],'halfwidth':.45,'height':2,'mode':'R1 modeled tread-center route'})
obstacles=[];ground=[]
for r in rows:
 if not r['visible'] or r['hide_render']:continue
 vs=r['vertices'];lo=min(v[2] for v in vs);hi=max(v[2] for v in vs)
 if r['name'].startswith('CAL_GROUND_'):
  ground.extend(Polygon([vs[i][:2] for i in f]) for f in r['faces'] if all(abs(vs[i][2]-hi)<1e-5 for i in f));continue
 # Orthogonal columns/equipment represented by their convex footprint; concave partitions conservative candidates only.
 g=MultiPoint([v[:2] for v in vs]).convex_hull
 if g.geom_type=='Polygon':obstacles.append((r['name'],g,lo,hi))
conflicts=[]
for p in paths:
 line=LineString([p['a'][:2],p['b'][:2]]);area=line.buffer(p['halfwidth'],cap_style=2)
 for name,g,lo,hi in obstacles:
  inter=area.intersection(g)
  if inter.is_empty or inter.area<.005:continue
  q=inter.representative_point();t=line.project(q)/line.length;z=p['a'][2]+t*(p['b'][2]-p['a'][2]);overlap=min(hi,z+p['height'])-max(lo,z+.1)
  if overlap>.1:conflicts.append({'path':p['id'],'obstacle':name,'xy':[q.x,q.y],'overlap_m2':inter.area,'vertical_overlap_m':overlap,'classification':'estimated_column' if name.startswith('COMP_') and ('_COL_' in name or 'COLUMN_' in name) else 'review_required','test':'Conservative footprint overlap and representative-point vertical interval; not continuous solid intersection'})
union=unary_union([g for g in ground if g.is_valid]);op=[]
for r in json.load(open(out/'openings_payload.json'))['openings']:
 g=shape(r['geometry']);op.append({'id':r['id'],'remaining_ground_overlap_m2':union.intersection(g.buffer(-.003)).area,'status':'Model opening only; actual entry footprint not independently surveyed'})
(out/'checked_paths.json').write_text(json.dumps(paths,ensure_ascii=False,indent=2))
result={'paths_checked':len(paths),'conflict_candidates':conflicts,'ground_openings':op,'limitations':['No full turning-radius vehicle simulation','Footprint proxy can overreport concave partitions','Previously identified real/unverified bridge supports are not relocated by this check']};(out/'flow_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print({'paths':len(paths),'conflicts':len(conflicts),'generic_columns':len({c['obstacle'] for c in conflicts if c['classification']=='estimated_column'}),'blocked_ground_openings':sum(o['remaining_ground_overlap_m2']>.01 for o in op)})
