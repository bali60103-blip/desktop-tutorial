import bpy,os,pathlib,json
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';folder=out/'mapped_vent_reviews';folder.mkdir(exist_ok=True);sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];review=bpy.data.scenes.get('MAPPED_VENT_DETAIL_REVIEW') or bpy.data.scenes.new('MAPPED_VENT_DETAIL_REVIEW');review.world=sc.world
if not review.camera:
 cd=bpy.data.cameras.new('MAPPED_VENT_REVIEW_CAMERA');cam=bpy.data.objects.new(cd.name,cd);review.collection.objects.link(cam);review.camera=cam
cam=review.camera;cam.data.type='ORTHO';review.render.engine='BLENDER_WORKBENCH';review.render.resolution_x=600;review.render.resolution_y=450;review.render.resolution_percentage=100;review.display.shading.color_type='MATERIAL';review.display.shading.show_shadows=False;review.display.shading.show_cavity=True;review.render.image_settings.file_format='PNG';rows=[]
try:
 for item in json.load(open(out/'mapped_vent_shell_report.json'))['items']:
  for o in list(review.collection.objects):
   if o.type=='MESH':review.collection.objects.unlink(o)
  o=bpy.data.objects[item['new_object']];review.collection.objects.link(o);bpy.context.window.scene=review;review.view_layers[0].update();bb=[o.matrix_world@Vector(v) for v in o.bound_box];center=sum(bb,Vector())/8;span=max(o.dimensions);cam.location=center+Vector((1,-1.4,.9))*span;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=span*2.0;cam.data.clip_end=max(1000,span*10);review.render.filepath=str(folder/(item['osm_id']+'.png'));bpy.ops.render.render(write_still=True,scene=review.name);rows.append({'osm_id':item['osm_id'],'file':item['osm_id']+'.png','status':'Estimated model-only review; not street-photo comparison'})
finally:bpy.context.window.scene=sc;sc.frame_set(1)
(out/'mapped_vent_render_index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={'rendered':len(rows),'scene_restored':sc.name}
