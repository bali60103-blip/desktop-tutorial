import bpy,os
sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc
states=[]
def reveal_roofs(lc):
 if lc.collection.name=='COMPLETION_REMOVABLE_ROOFS':states.append((lc,lc.exclude));lc.exclude=False
 for child in lc.children:reveal_roofs(child)
reveal_roofs(sc.view_layers[0].layer_collection);sc.view_layers[0].update()
try:
 """Comparison only: search displacement avoiding mapped underground mall geometry, not other site constraints."""
 import bpy,json,pathlib,os
 from mathutils import Vector
 from mathutils.bvhtree import BVHTree
 root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];paths=[p for p in json.load(open(root/'Calibration/checked_paths.json')) if p['id'].startswith('CORE_\u516c\u4e2d_0_')];a=Vector(paths[0]['a']);t=Vector(paths[0]['b'])-a;t.z=0;t.normalize();vv=[];ff=[];owner=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in sc.objects:
  if o.type!='MESH':continue
  if not (o.name.startswith(('CAL_SECONDARY_Y_','CAL_SECONDARY_Zhongshan_','Y_WORKING_FLOOR_','Zhongshan_Underground_Street_'))):continue
  e=o.evaluated_get(dg);m=e.to_mesh();off=len(vv);vv.extend([o.matrix_world@v.co for v in m.vertices]);ff.extend([[off+i for i in p.vertices] for p in m.polygons]);owner.extend([o.name]*len(m.polygons));e.to_mesh_clear()
 bvh=BVHTree.FromPolygons(vv,ff);candidates=[]
 for shift in range(0,61,5):
  offset=t*shift;hits=[]
  for p in paths:
   a=Vector(p['a'])+offset;b=Vector(p['b'])+offset;d=b-a;n=Vector((-d.y,d.x,0)).normalized()
   for j in range(1,20):
    for side in [-.8,0,.8]:
     q=a.lerp(b,j/20)+n*(side*p['halfwidth'])+Vector((0,0,.2));loc,normal,idx,dist=bvh.ray_cast(q,Vector((0,0,1)),p['height']-.2)
     if idx is not None:hits.append({'path':p['id'],'object':owner[idx]})
  candidates.append({'along_offset_m':shift,'translation':list(offset),'mall_hit_samples':len(hits),'blocked_paths':sorted(set(h['path'] for h in hits))})
 free=next((r for r in candidates if r['mall_hit_samples']==0),None);report={'scope':'Six public-parking core paths vs selected Y/Zhongshan mall meshes only, including roofs; 342 upward samples per candidate. Parking slabs, shafts, ground/road openings, property boundaries, piers, utilities and route connections not checked.','candidates':candidates,'first_mall_clear_candidate':free,'adopted':False};(out/'gongzhong_offset_comparison.json').write_text(json.dumps(report,indent=2));result=report
finally:
 for lc,value in states:lc.exclude=value
 sc.view_layers[0].update()
