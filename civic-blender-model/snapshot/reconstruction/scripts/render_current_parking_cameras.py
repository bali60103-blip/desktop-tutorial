import bpy,json,pathlib,os
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';folder=out/'underground_review_0912';folder.mkdir(exist_ok=True);source=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];name='PARKING_ROUTE_REVIEW_CURRENT_0912';old=bpy.data.scenes.get(name)
if old:bpy.data.scenes.remove(old)
review=source.copy();review.name=name;review.use_fake_user=True;review.timeline_markers.clear();ids={r['name'] for r in json.load(open(out.parent/'Calibration/camera_review_index.json')) if not r['name'].startswith('CIVIC200_')};cams=sorted([o for o in source.objects if o.type=='CAMERA' and o.name in ids],key=lambda o:o.name);review.render.engine='BLENDER_WORKBENCH';review.render.resolution_x=640;review.render.resolution_y=360;review.render.resolution_percentage=100;review.display.shading.show_shadows=False;review.display.shading.show_cavity=True;review.render.image_settings.file_format='PNG';rows=[]
try:
 for cam in cams:
  review.camera=cam;review.render.filepath=str(folder/(cam.name+'.png'));bpy.ops.render.render(write_still=True,scene=review.name);rows.append({'name':cam.name,'file':cam.name+'.png','position':list(cam.location),'scope':'Model-only review after bottom-floor closure; cutaway roofs hidden, physical ceiling clearance checked separately'})
finally:bpy.context.window.scene=source;source.frame_set(1)
assert len([m for m in source.timeline_markers if m.name.startswith('EW_1SEC_')])==106;(out/'underground_camera_review_0912.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={'rendered':len(rows),'animation_preserved':True,'review_scene':review.name}
