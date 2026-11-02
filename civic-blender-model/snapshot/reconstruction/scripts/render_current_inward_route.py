"""Render route camera markers; frame selection is required after camera animation binding."""
import bpy,os,pathlib,json,math
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';out=root/'inward_route_renders';out.mkdir(exist_ok=True);sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;markers=sorted((m for m in sc.timeline_markers if m.name.startswith('EW_1SEC_')),key=lambda m:m.frame);start=int(os.environ.get('CIVIC_RENDER_START','0'));end=int(os.environ.get('CIVIC_RENDER_END',str(len(markers))));rows=[];old=(sc.render.engine,sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,sc.render.filepath,sc.display.shading.show_shadows,sc.frame_current)
try:
 sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=640;sc.render.resolution_y=360;sc.render.resolution_percentage=100;sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True;sc.render.image_settings.file_format='PNG'
 for m in markers[start:end]:
  sc.frame_set(m.frame);assert sc.camera==m.camera;sc.render.filepath=str(out/(m.camera.name+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name);rows.append({'camera':m.camera.name,'frame':m.frame,'file':pathlib.Path(sc.render.filepath).name,'position':list(m.camera.location),'direction':m.camera.get('direction'),'scope':'Current inward-facing model view, not real-image calibration'})
finally:
 sc.render.engine,sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,sc.render.filepath,sc.display.shading.show_shadows,frame=old;sc.frame_set(frame)
(root/('inward_route_batch_'+str(start)+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2));result={'start':start,'end':end,'rendered':len(rows),'total':len(markers)}
