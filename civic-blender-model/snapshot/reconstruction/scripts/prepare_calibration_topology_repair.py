import json,pathlib,runpy,collections
from shapely.geometry import Polygon,Point
from shapely import set_precision
from shapely.ops import unary_union
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Calibration');p=json.load(open(root/'openings_payload.json'));r=next(r for r in p['parts'] if r['name']=='CAL_GROUND_ROADS_OFFICIAL_XY_0');vs=r['mesh']['vertices'];top=max(v[2] for v in vs);bottom=min(v[2] for v in vs);g=unary_union([Polygon([vs[i][:2] for i in f]) for f in r['mesh']['faces'] if all(abs(vs[i][2]-top)<1e-5 for i in f)]);fixed=set_precision(g.difference(Point(5950.924,895.367).buffer(.02)),.001);mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh'];parts=[]
for i,q in enumerate([fixed] if fixed.geom_type=='Polygon' else fixed.geoms):
 m=mesh(q,bottom,top);ec=collections.Counter(tuple(sorted((f[j],f[(j+1)%len(f)]))) for f in m['faces'] for j in range(len(f)))
 if any(n!=2 for n in ec.values()):
  print([(k,n,[m['vertices'][v] for v in k]) for k,n in ec.items() if n!=2][:10]);raise RuntimeError('Still nonmanifold')
 parts.append({'name':r['name']+'_FIX'+str(i),'mesh':m})
res={'replaces':r['name'],'parts':parts,'method':'20mm local disk cut separates zero-width contact; local mesh origins retained','changed_area_m2':g.symmetric_difference(fixed).area};(root/'topology_repair.json').write_text(json.dumps(res));print({k:v for k,v in res.items() if k!='parts'})
