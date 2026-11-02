import os
import bpy,json,pathlib,collections,math
from mathutils import Vector
out=(pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3');sc=bpy.context.scene;expected=json.load(open(out/'facade_payload.json'))+json.load(open(out/'minlevel_payload.json'));issues=[];checked=[]
for r in expected:
 o=bpy.data.objects.get('BLOCK_'+r['osm_id']+'_CORE')
 if not o:issues.append({'id':r['osm_id'],'issue':'missing core'});continue
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 if any(not math.isfinite(x) for v in vs for x in v):issues.append({'id':r['osm_id'],'issue':'nonfinite'})
 ed=collections.Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in o.data.polygons for i in range(len(p.vertices)))
 if any(n!=2 for n in ed.values()):issues.append({'id':r['osm_id'],'issue':'nonmanifold'})
 z0=min(v.z for v in vs);expected_z=min(v[2] for m in r['cores'] for v in m['vertices'])
 if abs(z0-expected_z)>.002:issues.append({'id':r['osm_id'],'issue':'base mismatch','actual':z0,'expected':expected_z})
 f=bpy.data.objects.get('BLOCK_'+r['osm_id']+'_FACADE')
 if f and len(f.data.vertices)!=len(r['points']):issues.append({'id':r['osm_id'],'issue':'point count mismatch'})
 checked.append({'id':r['osm_id'],'base_z':z0,'top_z':max(v.z for v in vs),'facade_points':len(r['points'])})
result={'checked_records':len(checked),'issues':issues,'records':checked,'model':bpy.data.filepath,'status':'Geometric/source-tag consistency only; no claim all elevations photo verified'};(out/'model_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));result={k:v for k,v in result.items() if k!='records'}
