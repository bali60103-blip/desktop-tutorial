import json,pathlib,os,collections
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';rows=json.load(open(out/'parking_horizontal_faces.json'));groups=collections.defaultdict(list)
for r in rows:
 p=Polygon(r['xy'])
 if p.is_valid and p.area>.001:groups[(r['object'],round(r['z'],2))].append(p)
keys=list(groups);polys=[unary_union(groups[k]) for k in keys];tree=STRtree(polys);matches=[]
for i,p in enumerate(polys):
 for j in tree.query(p):
  j=int(j)
  if j<=i or keys[i][0]==keys[j][0] or abs(keys[i][1]-keys[j][1])>.02:continue
  a=p.intersection(polys[j]).area
  if a>.05:matches.append({'a':keys[i][0],'b':keys[j][0],'z_a':keys[i][1],'z_b':keys[j][1],'overlap_m2':round(a,3),'fraction_a':round(a/p.area,4),'fraction_b':round(a/polys[j].area,4)})
r={'scope':'Visible selected parking-related horizontal mesh faces only; 2cm elevation grouping, >0.05m2 plan intersection. Not a swept-path or structural check.','pairs':sorted(matches,key=lambda x:-x['overlap_m2']),'horizontal_groups':len(keys)};(out/'parking_surface_overlap.json').write_text(json.dumps(r,indent=2));print(json.dumps({'pairs':len(matches),'largest':r['pairs'][:12]},indent=2))
