"""Measure candidate support-to-support spans in the CURRENT MODEL, never as-built heights.
Run after exporting span_height_context.json. Does not alter existing geometry.
"""
import bpy,json,math,os,csv
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
ctx=json.load(open(os.path.join(ROOT,'span_height_context.json')))
scene=bpy.data.scenes[ctx['scene']]
paths=ctx['paths'];piers=ctx['piers']
def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
for p in paths:
 p['chain']=[0.]
 for a,b in zip(p['points'],p['points'][1:]):p['chain'].append(p['chain'][-1]+dist(a,b))
 p['length']=p['chain'][-1];p['supports']=[]
def project(pt,p):
 best=None
 for i,(a,b) in enumerate(zip(p['points'],p['points'][1:])):
  dx,dy=b[0]-a[0],b[1]-a[1];l2=dx*dx+dy*dy
  if l2<1e-12:continue
  t=max(0.,min(1.,((pt[0]-a[0])*dx+(pt[1]-a[1])*dy)/l2))
  q=[a[0]+t*dx,a[1]+t*dy];d=dist(pt,q);v=(d,p['chain'][i]+t*math.sqrt(l2))
  if best is None or v[0]<best[0]:best=v
 return best
def at(p,s):
 s=max(0,min(p['length'],s))
 for i in range(len(p['chain'])-1):
  if s<=p['chain'][i+1]+1e-8:
   a,b=p['points'][i:i+2];l=p['chain'][i+1]-p['chain'][i]
   if l<1e-8:continue
   t=(s-p['chain'][i])/l;return [a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])],[(b[0]-a[0])/l,(b[1]-a[1])/l]
 return p['points'][-1],[1,0]
unassigned=[];ambiguous=[]
for pier in piers:
 choices=[]
 for idx,p in enumerate(paths):
  hit=project(pier['xy'],p)
  if hit and hit[0]<=p['width']/2+2:choices.append((hit[0],idx,hit[1]))
 choices.sort()
 if not choices:unassigned.append(pier['name']);continue
 d,idx,ss=choices[0];amb=len(choices)>1 and choices[1][0]-d<1.
 q={'pier':pier['name'],'s':ss,'lateral_distance':d,'ambiguous':amb}
 paths[idx]['supports'].append(q)
 if amb:ambiguous.append({'pier':pier['name'],'candidates':[{'deck':paths[i]['deck'],'distance':round(dd,3)} for dd,i,_ in choices[:3]]})
for p in paths:
 groups=[]
 for q in sorted(p['supports'],key=lambda x:x['s']):
  if groups and abs(q['s']-groups[-1]['s'])<2.5:
   g=groups[-1];g['members'].append(q);g['s']=sum(x['s'] for x in g['members'])/len(g['members'])
  else:groups.append({'s':q['s'],'members':[q]})
 p['groups']=groups
spans=[]
for p in paths:
 for a,b in zip(p['groups'],p['groups'][1:]):
  if b['s']-a['s']<3:continue
  spans.append({'deck':p['deck'],'path':p,'start':a,'end':b,'length':b['s']-a['s'],'boundary':False})
# Boundary spans only when exactly two mapped path endpoints meet.
endpoint_groups=[]
for p in paths:
 for side in [0,1]:
  xy=p['points'][0 if side==0 else -1]
  found=next((g for g in endpoint_groups if dist(g['xy'],xy)<.5),None)
  if found is None:found={'xy':xy,'ends':[]};endpoint_groups.append(found)
  found['ends'].append((p,side))
boundary_review=[]
for g in endpoint_groups:
 ends=g['ends']
 if len(ends)!=2:
  if len(ends)>1:boundary_review.append({'decks':[p['deck'] for p,_ in ends],'reason':'branching endpoint; support pairing needs review'})
  continue
 (p,side),(q,other)=ends
 if not p['groups'] or not q['groups']:continue
 ga=p['groups'][0 if side==0 else -1];gb=q['groups'][0 if other==0 else -1]
 da=ga['s'] if side==0 else p['length']-ga['s'];db=gb['s'] if other==0 else q['length']-gb['s']
 if da+db<3 or da+db>100:
  boundary_review.append({'decks':[p['deck'],q['deck']],'reason':'boundary support gap outside 3–100m review range'});continue
 pa,_=at(p,ga['s']);pb,_=at(q,gb['s'])
 # Retain original polylines through the shared endpoint, not a straight chord.
 segA=[pa]+[v for v,c in zip(p['points'],p['chain']) if (c<ga['s'] if side==0 else c>ga['s'])]
 if side==0:segA=[pa]+list(reversed([v for v,c in zip(p['points'],p['chain']) if c<ga['s']]))
 segB=[v for v,c in zip(q['points'],q['chain']) if (c<gb['s'] if other==0 else c>gb['s'])]
 if other==1:segB=list(reversed(segB))
 pts=segA+segB+[pb];clean=[pts[0]]
 for v in pts[1:]:
  if dist(v,clean[-1])>.001:clean.append(v)
 cp={'points':clean,'chain':[0.],'width':min(p['width'],q['width'])}
 for a,b in zip(clean,clean[1:]):cp['chain'].append(cp['chain'][-1]+dist(a,b))
 cp['length']=cp['chain'][-1]
 spans.append({'deck':p['deck']+'|'+q['deck'],'path':cp,'start':ga,'end':gb,'length':cp['length'],'boundary':True})
cache={}
def tree(o):
 if o.name not in cache:
  dg=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(dg);m=e.to_mesh()
  vs=[e.matrix_world@v.co for v in m.vertices];fs=[list(f.vertices) for f in m.polygons]
  cache[o.name]=BVHTree.FromPolygons(vs,fs);e.to_mesh_clear()
 return cache[o.name]
def bounds(o):
 ps=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [min(v[i] for v in ps) for i in range(3)],[max(v[i] for v in ps) for i in range(3)]
grounds=[]
for o in scene.objects:
 if o.type=='MESH' and (o.name.startswith('CAL_GROUND_ROADS_OFFICIAL_XY') or o.name.startswith('CAL_GROUND_MEDIAN_WORKING') or o.name.startswith('UB_MEDIAN_0_WITH')):
  grounds.append((o,*bounds(o)))
def zhit(o,x,y,up=False,z=100):
 hit=tree(o).ray_cast(Vector((x,y,z)),Vector((0,0,1 if up else -1)),200)
 return float(hit[0].z) if hit[0] is not None else None
reports=[]
for n,sp in enumerate(spans):
 p=sp['path'];decks=[scene.objects[name] for name in sp['deck'].split('|')]
 ids=[d.name[5:] for d in decks]
 beams=[o for o in scene.objects if o.type=='MESH' and any(o.name.startswith('GIRDER_'+k+'_') for k in ids)]
 rows=[];flags=[]
 if any(x['ambiguous'] for g in [sp['start'],sp['end']] for x in g['members']):flags.append('ambiguous_pier_to_deck_assignment')
 if sp['length']>60:flags.append('long_gap_check_missing_supports')
 for t in [i/10 for i in range(11)]:
  ss=t*p['length'] if sp['boundary'] else sp['start']['s']+t*sp['length']
  xy,tan=at(p,ss);cross=[]
  for j in range(9):
   offset=(j-4)*p['width']*.105;x=xy[0]-tan[1]*offset;y=xy[1]+tan[0]*offset
   dz=[z for d in decks if (z:=zhit(d,x,y)) is not None]
   if not dz:continue
   gz=[z for o,lo,hi in grounds if lo[0]-.01<=x<=hi[0]+.01 and lo[1]-.01<=y<=hi[1]+.01 and (z:=zhit(o,x,y,z=30)) is not None]
   ground=max(gz) if gz else None
   soff=[z for o in beams+decks if (z:=zhit(o,x,y,True,z=-20)) is not None]
   low=min(soff) if soff else None
   cross.append({'offset_m':round(offset,3),'xy':[round(x,3),round(y,3)],'ground_z':ground,'deck_top_z':max(dz),'soffit_z':low,'clearance_m':low-ground if low is not None and ground is not None else None})
  vals=[x['clearance_m'] for x in cross if x['clearance_m'] is not None]
  rows.append({'fraction':t,'xy':[round(v,3) for v in xy],'sampled_min_clearance_m':min(vals) if vals else None,'cross_samples':cross})
 if any(any(v['ground_z'] is None for v in x['cross_samples']) for x in rows):flags.append('ground_surface_missing_at_some_samples')
 if any(not x['cross_samples'] for x in rows):flags.append('deck_ray_miss_at_some_stations')
 vals=[x['sampled_min_clearance_m'] for x in rows if x['sampled_min_clearance_m'] is not None]
 tops=[v['deck_top_z'] for x in rows for v in x['cross_samples']]
 reports.append({'span_id':'SPAN_MODEL_%03d'%n,'decks':sp['deck'].split('|'),'start_piers':[v['pier'] for v in sp['start']['members']],'end_piers':[v['pier'] for v in sp['end']['members']],'plan_length_m':sp['length'],'boundary_span':sp['boundary'],'sampled_min_clearance_m':min(vals) if vals else None,'deck_top_z_min':min(tops) if tops else None,'deck_top_z_max':max(tops) if tops else None,'flags':flags,'samples':rows,'real_world_verified':False})
out={'measurement_basis':'Blender geometry in meters; scene Z is not established as an absolute elevation datum','spans':reports,'pier_count':len(piers),'assigned_piers':len(piers)-len(unassigned),'unassigned_piers':unassigned,'ambiguous_assignments':ambiguous,'boundary_review':boundary_review,'sampling':'11 longitudinal stations × 9 transverse positions per candidate span; sampled minimum is not guaranteed continuous minimum','support_grouping':'Nearest mapped deck centerline; columns within 2.5m longitudinal position grouped as a candidate bent. All support associations unverified.','not_included':['actual surveyed elevations','hidden utilities reducing real clearance','cross beams or bearing pads outside the GIRDER/DECK families','unresolved branching endpoint spans'],'full_height_verification_complete':False}
json.dump(out,open(os.path.join(ROOT,'span_height_audit.json'),'w'),ensure_ascii=False,indent=2)
with open(os.path.join(ROOT,'span_height_audit.csv'),'w',newline='',encoding='utf-8-sig') as f:
 wr=csv.writer(f);wr.writerow(['span_id','decks','start_piers','end_piers','plan_length_m','sampled_min_clearance_m','deck_top_z_min','deck_top_z_max','flags','real_world_verified'])
 for r in reports:wr.writerow([r['span_id'],'|'.join(r['decks']),'|'.join(r['start_piers']),'|'.join(r['end_piers']),r['plan_length_m'],r['sampled_min_clearance_m'],r['deck_top_z_min'],r['deck_top_z_max'],'|'.join(r['flags']),False])
result={'candidate_spans':len(reports),'assigned_piers':len(piers)-len(unassigned),'unassigned_piers':len(unassigned),'ambiguous_assignments':len(ambiguous),'branching_endpoints':len(boundary_review),'with_clearance':sum(r['sampled_min_clearance_m'] is not None for r in reports),'full_height_verification_complete':False}
