import bpy,os,pathlib,json
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];oldcam=sc.camera;oldshadow=sc.display.shading.show_shadows;oldcavity=sc.display.shading.show_cavity;oldpath=sc.render.filepath
try:
 sc.camera=bpy.data.objects['\u4e2d\u6797_B1_B2_CAMERA'];sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=bool(globals().get('DIAGNOSTIC_CAVITY',False));sc.render.filepath=str(out/('ZHONGLIN_CAVITY_ONLY_DIAGNOSTIC.png' if globals().get('DIAGNOSTIC_CAVITY',False) else 'ZHONGLIN_NO_SHADOW_DIAGNOSTIC.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
finally:sc.camera=oldcam;sc.display.shading.show_shadows=oldshadow;sc.display.shading.show_cavity=oldcavity;sc.render.filepath=oldpath
result={'diagnostic':'Workbench shadows/cavity disabled only for comparison; geometry unchanged'}
