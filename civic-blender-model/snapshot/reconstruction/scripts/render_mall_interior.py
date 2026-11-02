import bpy,json,pathlib
from mathutils import Vector
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/UndergroundShells');sc=bpy.data.scenes['UNDERGROUND_SHELL_COMPARISON'];col=bpy.data.collections['UNDERGROUND_SHELLS_ESTIMATED'];cam=sc.camera
for o in col.objects:o.hide_render=o['source_object']!='Zhongshan_Underground_Street_中山地下街'
f=bpy.data.objects['Zhongshan_Underground_Street_中山地下街_FLOOR'];vs=[v.co for v in f.data.vertices];xmin=min(v.x for v in vs);xmax=max(v.x for v in vs);ymax=max(v.y for v in vs)
# Northern straight portion of legacy footprint, oblique close inspection of floor and wall; roof off for cutaway.
for o in col.objects:
 if 'REMOVABLE_ROOF' in o.name:o.hide_render=True
cam.location=(xmax+25,ymax-50,24);target=Vector((xmax-8,ymax-35,-2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=85;cam.data.clip_start=.1;sc.render.filepath=str(out/'zhongshan_shell_detail.png');bpy.ops.render.render(write_still=True,scene=sc.name)
for o in col.objects:o.hide_render='REMOVABLE_ROOF' in o.name
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'detail_render':str(out/'zhongshan_shell_detail.png'),'note':'Cutaway of legacy footprint. No entrance connectivity asserted.'}
