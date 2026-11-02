import json,pathlib,runpy,collections,math
from shapely.geometry import Polygon,shape
from shapely.ops import unary_union
from shapely import set_precision,make_valid
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Calibration');opens=json.load(open(out/'openings_payload.json'))['openings'];allcuts=unary_union([shape(r['geometry']) for r in opens]);r1=unary_union([shape(r['geometry']) for r in opens if r['id']=='R1']);mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh'];rows=json.load(open(out/'secondary_opening_surfaces.json'))+[r for r in json.load(open(out/'evaluated_roofs.json')) if r['name'] in ['Y_REMOVABLE_ROOF_0','Zhongshan_Underground_Street_中山地下街_REMOVABLE_ROOF']];parts=[];reports=[]
for r in rows:
 vs=r['vertices'];top=max(v[2] for v in vs);bottom=min(v[2] for v in vs);pp=[]
 for f in r['faces']:
  if all(abs(vs[i][2]-top)<1e-5 for i in f):
   q=Polygon([vs[i][:2] for i in f])
   if q.is_valid and q.area>1e-8:pp.append(q)
 old=set_precision(unary_union(pp),.001);cut=r1 if 'ROOF' in r['name'] else allcuts;new=set_precision(make_valid(old.difference(cut)),.001);changed=old.area-new.area
 if changed<.00001:continue
 for i,p in enumerate([new] if new.geom_type=='Polygon' else new.geoms):
  if p.geom_type!='Polygon' or p.area<.00001:continue
  m=mesh(p,bottom,top);ec=collections.Counter(tuple(sorted((f[j],f[(j+1)%len(f)]))) for f in m['faces'] for j in range(len(f)))
  if any(n!=2 for n in ec.values()):raise RuntimeError('Nonmanifold '+r['name'])
  parts.append({'name':'CAL_SECONDARY_'+r['name']+'_'+str(i),'replaces':r['name'],'mesh':m})
 reports.append({'source':r['name'],'removed_area_m2':changed,'z_range':[bottom,top],'status':'Estimated opening consistency only; ground marking conflicts remain location-review issues'})
# Batch disconnected components in 200m cells to keep local floating-point precision and avoid tens of thousands of objects.
groups={}
for p in parts:
 vs=p['mesh']['vertices'];x=sum(v[0] for v in vs)/len(vs);y=sum(v[1] for v in vs)/len(vs);key=(p['replaces'],math.floor(x/200),math.floor(y/200));q=groups.setdefault(key,{'name':'CAL_SECONDARY_'+p['replaces']+'_'+str(key[1])+'_'+str(key[2]),'replaces':p['replaces'],'mesh':{'vertices':[],'faces':[]}});offset=len(q['mesh']['vertices']);q['mesh']['vertices'].extend(vs);q['mesh']['faces'].extend([[i+offset for i in f] for f in p['mesh']['faces']])
parts=list(groups.values())
(out/'secondary_corrections.json').write_text(json.dumps({'parts':parts,'reports':reports},ensure_ascii=False));print({'new_parts':len(parts),'reports':reports})
