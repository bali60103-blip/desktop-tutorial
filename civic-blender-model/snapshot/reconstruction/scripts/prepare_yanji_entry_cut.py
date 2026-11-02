import json,pathlib,ast,collections
from shapely.geometry import Polygon,LineString,mapping
from shapely.ops import unary_union
from shapely import set_precision,constrained_delaunay_triangles
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/CalibrationRound2');out.mkdir(exist_ok=True)
r=json.load(open('/tmp/yanji_wall.json'));vs=r['vertices'];top=max(v[2] for v in vs);bottom=min(v[2] for v in vs)
g=unary_union([Polygon([vs[i][:2] for i in f]) for f in r['faces'] if all(abs(vs[i][2]-top)<1e-5 for i in f)])
p=next(p for p in json.load(open(out.parent/'Calibration/checked_paths.json')) if p['id']=='COMP_ACCESS_延吉_0')
cut=LineString([p['a'][:2],p['b'][:2]]).buffer(p['halfwidth']+.25,cap_style=2)
new=set_precision(g.difference(cut),.001)
# Reuse only the pure mesh builder, without running earlier artifact-generation code.
tree=ast.parse(pathlib.Path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='mesh');exec(compile(ast.Module(body=[fn],type_ignores=[]),'<mesh>','exec'))
parts=[]
for poly in ([new] if new.geom_type=='Polygon' else new.geoms):
 if poly.geom_type!='Polygon':continue
 m=mesh(poly,bottom,top);ec=collections.Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in m['faces'] for i in range(len(f)))
 assert all(n==2 for n in ec.values())
 parts.append(m)
r={'source_object':r['name'],'path':p,'opening_width_m':2*(p['halfwidth']+.25),'removed_plan_area_m2':g.area-new.area,'remaining_cut_overlap_m2':new.intersection(cut).area,'parts':parts,'status':'ESTIMATED opening following existing assumed ramp. Location, road width and actual structural opening unverified; not a real-world position calibration.'}
(out/'yanji_entry_cut.json').write_text(json.dumps(r,ensure_ascii=False));print({k:v for k,v in r.items() if k not in ['parts','path']})
