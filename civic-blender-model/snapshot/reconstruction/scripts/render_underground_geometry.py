"""Render geometry checks without Workbench shadow-map artifacts; not daylight analysis."""
import bpy,json,pathlib
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/UndergroundCavity')
sc=bpy.data.scenes['Scene'];bpy.context.window.scene=sc
sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=False
sc['inspection_render_note']='Studio geometry inspection without screen-space cavity or shadows; not daylight/occlusion analysis'
for frame,name in [(101,'RAMP_CAM_EAST_1F_B1'),(102,'RAMP_CAM_WEST_1F_B1'),(103,'RAMP_CAM_B1_B2')]:
 sc.frame_set(frame);sc.camera=bpy.data.objects[name];sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
sc.frame_set(103);sc.camera=bpy.data.objects['RAMP_CAM_B1_B2']
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'file':bpy.data.filepath,'render':'studio geometry only; shadows/cavity disabled'}
