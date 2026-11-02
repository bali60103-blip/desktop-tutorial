import bpy,json,os,pathlib,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];issues=[];objects=[]
for cname in ['CAL3_PARKING_STAIR_HANDRAILS','CAL3_PARKING_LANDING_GUARDS']:
 for o in bpy.data.collections[cname].objects:
  counts={}
  for p in o.data.polygons:
   for e in p.edge_keys:counts[e]=counts.get(e,0)+1
  if any(n!=2 for n in counts.values()):issues.append({'object':o.name,'issue':'nonmanifold_edge'})
  if any(not math.isfinite(x) for v in o.data.vertices for x in v.co):issues.append({'object':o.name,'issue':'nonfinite'})
  objects.append(o.name)
# Landing post centers must touch their actual landing tops.
miss=[]
for o in bpy.data.collections['CAL3_PARKING_LANDING_GUARDS'].objects:
 key=o['source_path'];_,section,core,level,_=key.split('_');source=bpy.data.objects['COMP_'+section+'_CORE'+core+'_L'+level[1:]+'_LANDING'];vs=[source.matrix_world@v.co for v in source.data.vertices];tree=BVHTree.FromPolygons(vs,[list(p.vertices) for p in source.data.polygons])
 for j in range(5):
  k=(3+j)*20;center=sum((o.matrix_world@o.data.vertices[k+i].co for i in range(10)),Vector())/10;hit,_,_,_=tree.ray_cast(center+Vector((0,0,.05)),Vector((0,0,-1)),.1)
  if hit is None or abs(hit.z-center.z)>.002:miss.append({'object':o.name,'post':j})
markers=[m for m in sc.timeline_markers if m.name.startswith('EW_1SEC_')];assert len(markers)==106;assert all(m.camera.get('direction')=='TOWARD_BOULEVARD_AXIS' for m in markers)
comparison=bpy.data.scenes['GONGZHONG_CORE_OFFSET_COMPARISON'];r={'mesh_objects_checked':len(objects),'mesh_issues':issues,'landing_post_seating_misses':miss,'flight_posts_seated':json.load(open(out/'handrail_seating_check.json'))['posts_seated'],'landing_posts_checked':140,'animation_markers_preserved':len(markers),'frame_range':[sc.frame_start,sc.frame_end],'inward_camera_directions_preserved':True,'comparison_adopted':False,'previously_reported_blocked_paths':15,'full_site_headroom_rerun':False};(out/'stair_detail_checkpoint.json').write_text(json.dumps(r,indent=2));meta=json.load(open(out/'gongzhong_comparison_model.json'));meta['counts']={k:sum(o.type=='MESH' and o.name.startswith('GZ_'+k+'_') for o in comparison.objects) for k in ['ORIGINAL','OFFSET_5M']};(out/'gongzhong_comparison_model.json').write_text(json.dumps(meta,indent=2));result=r
