import bpy,json,pathlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');p=json.load(open(root/'YMallEntrances/source/y_entrance_payload.json'));names=['GROUND_ROADS_OFFICIAL_XY','GROUND_ROADS_ESTIMATED_GAPS','GROUND_SIDEWALKS_WITH_ESTIMATED_RAMPS','GROUND_MEDIAN_WORKING_ESTIMATED'];trees={}
for name in names:
 o=bpy.data.objects[name];trees[name]=BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(f.vertices) for f in o.data.polygons])
rows=[]
for e in p['entries']:
 a=Vector(e['live_xy']);d=(Vector(e['lower_landing_xy'])-a).normalized();hits=[]
 for k in range(1,24):
  q=a+d*(k*.3)
  for name,t in trees.items():
   loc,_,_,dist=t.ray_cast(Vector((q.x,q.y,3)),Vector((0,0,-1)),5)
   if loc is not None:hits.append({'step':k,'surface':name,'z':loc.z})
 rows.append({'ref':e['ref'],'ground_hits':hits})
out=root/'YGroundOpenings';out.mkdir(exist_ok=True);(out/'ground_opening_audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
# Export horizontal/near-horizontal faces only for local surface patch, retaining source Z.
faces=[];xs=[e['live_xy'][0] for e in p['entries']];ys=[e['live_xy'][1] for e in p['entries']]
for name in names:
 o=bpy.data.objects[name]
 for f in o.data.polygons:
  v=[list(o.matrix_world@o.data.vertices[i].co) for i in f.vertices]
  if min(q[0] for q in v)>max(xs)+25 or max(q[0] for q in v)<min(xs)-25 or min(q[1] for q in v)>max(ys)+25 or max(q[1] for q in v)<min(ys)-25:continue
  if max(q[2] for q in v)-min(q[2] for q in v)<.0001 and min(q[2] for q in v)>=-.01:faces.append({'source':name,'vertices':v})
(out/'source_ground_faces.json').write_text(json.dumps(faces));result={'blocked_entries':[r['ref'] for r in rows if r['ground_hits']],'entries_without_ground_hits':[r['ref'] for r in rows if not r['ground_hits']],'patch_source_faces':len(faces),'note':'No-hit may mean missing ground coverage, not verified open stairwell.'}
