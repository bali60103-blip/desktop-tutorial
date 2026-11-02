"""Whole-bent translation candidates against modeled crossings and mapped Zhonglin access.
No structural approval, as-built location or complete corridor ramp coverage asserted.
"""
import json,pathlib,math
from shapely.geometry import Point,Polygon,LineString
from shapely.ops import unary_union
from pyproj import Transformer
R=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934')
report=json.load(open(R/'Worksheet04_05/stage45_check.json'));geo=json.load(open(R/'Gate_B_Review/support_geometry.json'));rows={x['name']:x for x in geo['supports']}
cp=json.load(open('/tmp/civic-ground-crossings/crossing_payload.json'))['meshes']['GROUND_CROSSWALK_MARKINGS_ESTIMATED'];vs=cp['vertices']
mark=unary_union([Polygon([(vs[i][0],vs[i][1]) for i in f]) for f in cp['faces'] if len(f)==3 and all(abs(vs[i][2]-.005)<1e-6 for i in f)]).buffer(1.5)
audit=json.load(open(R/'Stage03_Zhonglin/zhonglin_audit.json'));access=unary_union([LineString(r['live_xy']).buffer(3.5) for r in audit['routes']]);blocked=unary_union([mark,access])
mm=json.load(open(R/'GroundFull/median_source/median_payload.json'))['mesh'];mv=mm['vertices'];median=unary_union([Polygon([(mv[i][0],mv[i][1]) for i in f]) for f in mm['faces'] if len(f)==3 and all(abs(mv[i][2]-.18)<1e-6 for i in f)])
f=json.load(open(R/'registration.json'));g=f['live_to_twd97'];ang=math.radians(g['rotation_degrees']);origin=[f['origin_epsg3826'][i]+g['translation'][i] for i in (0,1)];tr=Transformer.from_crs(4326,3826,always_xy=True)
def loc(q):
 x,y=tr.transform(*q);x-=origin[0];y-=origin[1];return ((math.cos(ang)*x+math.sin(ang)*y)/g['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/g['scale'])
axes=[]
for ft in json.load(open('/tmp/civic-stage01/civic_all_named_ways.geojson'))['features']:
 t=ft['properties']
 if t.get('bridge')=='yes':axes.append((t,LineString([loc(q) for q in ft['geometry']['coordinates']])))
def center(r):
 p=r['vertices'];return [(min(q[i] for q in p)+max(q[i] for q in p))/2 for i in (0,1)]
groups=[]
for entry in report['local_support_checks']:
 cap=entry['cap'];names=[cap]+[d['hidden'] for d in report['duplicates'] if d['kept']==cap];piers=[n.replace('_CAP_ESTIMATED','') for n in names];piers=[n for n in piers if n in rows];xy=center(rows[cap]);points=[center(rows[n]) for n in piers]
 t,line=min(axes,key=lambda a:a[1].distance(Point(xy)));station=line.project(Point(xy));a=line.interpolate(max(0,station-1));b=line.interpolate(min(line.length,station+1));v=(b.x-a.x,b.y-a.y);length=math.hypot(*v);v=(v[0]/length,v[1]/length)
 def geom(delta):return unary_union([Point(p[0]+v[0]*delta,p[1]+v[1]*delta).buffer(1) for p in points])
 old=geom(0);conflict=old.intersection(blocked).area
 candidates=[]
 if conflict>.01:
  for shift in [sign*k for k in range(1,21) for sign in [-1,1]]:
   proposal=geom(shift);area=proposal.intersection(blocked).area
   if area>.01 or proposal.difference(median).area>.001:continue
   # Centerline envelope is only an initial broad check, not local deck support verification.
   lanes=t.get('lanes','3');width=(int(lanes) if str(lanes).isdigit() else 3)*3.25+2
   if any(Point(p[0]+v[0]*shift,p[1]+v[1]*shift).distance(line)>width/2-1 for p in points):continue
   candidates.append({'shift_m':shift,'delta_xy':[v[0]*shift,v[1]*shift],'remaining_overlap_m2':area})
 selected=min(candidates,key=lambda c:abs(c['shift_m'])) if candidates else None
 groups.append({'cap':cap,'piers':piers,'center_xy':xy,'original_overlap_m2':conflict,'candidate_options':candidates,'selected_for_comparison':selected,'status':'ESTIMATED ALTERNATIVE - structural spans, foundations and utilities unchecked'})
# Proximity change is reported explicitly; it is not a design-span certification.
for r in groups:
 xy=r['center_xy'];others=[q for q in groups if q is not r];r['nearest_other_bent_before_m']=min(math.dist(xy,q['center_xy']) for q in others)
 if r['selected_for_comparison']:
  d=r['selected_for_comparison']['delta_xy'];new=[xy[i]+d[i] for i in (0,1)];r['nearest_other_bent_after_m']=min(math.dist(new,[q['center_xy'][i]+(q['selected_for_comparison']['delta_xy'][i] if q['selected_for_comparison'] else 0) for i in (0,1)]) for q in others)
summary={'bent_groups':len(groups),'groups_intersecting_modeled_exclusions':sum(r['original_overlap_m2']>.01 for r in groups),'groups_with_translation_candidate':sum(r['selected_for_comparison'] is not None for r in groups),'unresolved_groups':sum(r['original_overlap_m2']>.01 and r['selected_for_comparison'] is None for r in groups)}
out={'summary':summary,'limitations':['User-selected hard constraint: full pier footprint inside inferred median, shifts limited to +/-20m along bridge axis','Crossing markings are inferred, with 1.5m buffer','Only six mapped Zhonglin access lines included, with assumed 3.5m exclusion radius','Bridge centerline width is estimated','Translations move a whole bent and cap together; spans, bearing contact and foundation conflicts require redesign','No available alternative is not proof that original position is safe'],'groups':groups}
p=R/'Worksheet04_05/pier_alternatives.json'
if p.exists():(R/'Worksheet04_05/pier_alternatives_first_pass_REJECTED.json').write_text(p.read_text())
p.write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(summary))
