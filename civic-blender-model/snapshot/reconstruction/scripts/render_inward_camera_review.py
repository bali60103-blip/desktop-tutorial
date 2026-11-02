import bpy,os,pathlib,json
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];cam=sc.camera;old=(sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,sc.render.filepath,sc.display.shading.show_shadows);files=[]
try:
 sc.render.resolution_x=800;sc.render.resolution_y=450;sc.render.resolution_percentage=100;sc.display.shading.show_shadows=False
 for name in ['CIVIC200_END_N','CIVIC200_END_S','CIVIC200_03K800_N','CIVIC200_03K800_S','CIVIC200_00K000_N','CIVIC200_00K000_S']:
  sc.frame_set(next(m.frame for m in sc.timeline_markers if m.camera and m.camera.name==name));assert sc.camera.name==name;sc.render.filepath=str(out/('INWARD_'+name+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name);files.append(pathlib.Path(sc.render.filepath).name)
finally:
 sc.camera=cam;sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage,sc.render.filepath,sc.display.shading.show_shadows=old;sc.frame_set(1)
result={'renders':files}
