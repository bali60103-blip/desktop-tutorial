import bpy,json,pathlib,datetime
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';p=json.load(open(out/'payload.json'));stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];cols={k:bpy.data.collections['COMPLETION_'+k] for k in ['GROUND_HIGHWAY','FRONTAGE','PARKING','MARKINGS','EQUIPMENT','MALLS','REMOVABLE_ROOFS','ISSUE_MARKERS']};qa=p['parts'];cam=bpy.data.objects['FRONTAGE_HEIGHT_CAMERA']
bpy.context.window.scene=sc
sc.view_layers[0].update()
cols['REMOVABLE_ROOFS']['instructions']='Toggle collection for above-ground / underground cutaway; roof heights assumed.';sc.view_layers[0].layer_collection.children[cols['REMOVABLE_ROOFS'].name].exclude=True
old=cam.matrix_world.copy();scale=cam.data.ortho_scale
try:
 for label,center,offset,width in [('全段',Vector((4800,850,0)),Vector((0,-8500,8000)),11500),('中林地下',Vector((1200,730,-3.6)),Vector((60,-90,95)),165)]:
  cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=width;sc.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
finally:cam.matrix_world=old;cam.data.ortho_scale=scale
bpy.context.window.scene=sc
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  sp=area.spaces.active;sp.clip_end=30000;sp.region_3d.view_location=(4800,850,0);sp.region_3d.view_distance=9000
file=out/('CIVIC_COMPLETION_WORKING_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'scene':sc.name,'new_meshes':len(qa),'group_counts':p['counts'],'new_mesh_nonmanifold_edges':0,'issue_markers':len(cols['ISSUE_MARKERS'].objects),'total_scene_objects':len(sc.objects),'limits':'Working source-covered geometry only; layout, elevations, landmark heights and entrances remain estimated. Some retained underground alternatives overlap. Satellite/streetview calibration deferred per user.'};(out/'build_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
