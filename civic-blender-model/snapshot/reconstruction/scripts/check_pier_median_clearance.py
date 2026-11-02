"""Read-only second-pass rejection check against inferred median footprint."""
import pathlib,json
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');p=json.load(open(root/'Worksheet04_05/pier_alternatives.json'));m=json.load(open(root/'GroundFull/median_source/median_payload.json'))['mesh'];v=m['vertices'];median=unary_union([Polygon([(v[i][0],v[i][1]) for i in f]) for f in m['faces'] if len(f)==3 and all(abs(v[i][2]-.18)<1e-6 for i in f)])
g={r['name']:r for r in json.load(open(root/'Gate_B_Review/support_geometry.json'))['supports']};rows=[]
for r in p['groups']:
 if not r['selected_for_comparison']:continue
 d=r['selected_for_comparison']['delta_xy'];circles=[]
 for name in r['piers']:
  vs=g[name]['vertices'];xy=[(min(q[i] for q in vs)+max(q[i] for q in vs))/2+d[i] for i in (0,1)];circles.append(Point(xy).buffer(1))
 footprint=unary_union(circles);outside=footprint.difference(median).area
 rows.append({'cap':r['cap'],'shift_m':r['selected_for_comparison']['shift_m'],'outside_inferred_median_m2':outside,'status':'REJECT FOR ADOPTION: outside inferred median; vehicle-space conflict unresolved' if outside>.01 else 'Inside inferred median only; still not field/structurally verified'})
report={'checks':rows,'scope':'Second-pass spatial screening. Inferred median is not proof of actual lane boundary. Original and alternative retained only for comparison.'};(root/'Worksheet04_05/median_clearance_check.json').write_text(json.dumps(report,indent=2));print(json.dumps(rows))
