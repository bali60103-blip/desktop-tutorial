import bpy,json,pathlib,os,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';working=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];scene=bpy.data.scenes['YANJI_PHOTO_COMPARISON_ESTIMATED'];targets=list(bpy.data.collections['CAL3_MACHINE_ROOM_DOORS'].objects)+[o for o in bpy.data.collections['CAL3_YANJI_PHOTO_COMPARISON'].objects if o.type=='MESH' and o.name.startswith(('YANJI_DETAIL_','YANJI_RECESSED_','YANJI_DRAIN_CHANNEL_'))];issues=[]
for o in targets:
 counts={}
 for p in o.data.polygons:
  for e in p.edge_keys:counts[e]=counts.get(e,0)+1
 if any(n!=2 for n in counts.values()):issues.append({'object':o.name,'type':'nonmanifold_edge'})
 if any(not math.isfinite(c) for v in o.data.vertices for c in v.co):issues.append({'object':o.name,'type':'nonfinite'})
bpy.context.window.scene=scene;scene.view_layers[0].update();vv=[];ff=[];owner=[]
for o in scene.objects:
 if o.type!='MESH':continue
 off=len(vv);vv.extend([o.matrix_world@v.co for v in o.data.vertices]);ff.extend([[off+i for i in p.vertices] for p in o.data.polygons]);owner.extend([o.name]*len(o.data.polygons))
tree=BVHTree.FromPolygons(vv,ff);anchor=Vector((4215.1324,348.2492,0));angle=math.atan2(-5.75,55);d=Vector((math.cos(angle),math.sin(angle),0));n=Vector((-d.y,d.x,0));drains=[]
for tag,x,y,z in [('UPPER',-.8,0,0),('LOWER',53.5,.8*(55-53.5)/25,-1.8-1.8*(53.5-30)/25)]:
 pos=anchor+d*x+n*(y+.05)+Vector((0,0,z+.1));hit,_,idx,dist=tree.ray_cast(pos,Vector((0,0,-1)),1);name=owner[idx] if idx is not None else None;depth=z-hit.z if hit is not None else None;ok=name=='YANJI_DRAIN_CHANNEL_'+tag+'_BASE' and abs(depth-.13)<.002;drains.append({'drain':tag,'hit_object':name,'depth_below_ramp_m':depth,'pass':ok})
 if not ok:issues.append({'drain':tag,'type':'drain_slot_not_open'})
scene.display.shading.show_shadows=False;bpy.ops.render.render(write_still=True,scene=scene.name);markers=[m for m in working.timeline_markers if m.name.startswith('EW_1SEC_')];assert len(markers)==106 and all(m.camera.get('direction')=='TOWARD_BOULEVARD_AXIS' for m in markers);bpy.context.window.scene=working;working.frame_set(1);r={'checked_meshes':len(targets),'issues':issues,'drain_slot_checks':drains,'machine_rooms_detailed':16,'animation_camera_cuts_preserved':106,'frame_range':[working.frame_start,working.frame_end],'full_site_headroom_rerun':False,'comparison_adopted':False};(out/'room_yanji_detail_check.json').write_text(json.dumps(r,indent=2));result=r
