"""Inside Blender, ground-only review renders with elevated visibility restored afterward."""
import bpy,json,pathlib
from mathutils import Vector
root=pathlib.Path(ROOT);sc=bpy.context.scene;cam=bpy.data.objects['GROUND_FULL_CAMERA'];before={};objects_before={}
for col in bpy.data.collections:
 if col.name.startswith(('04_Elevated','05_Parapets','06_Steel','07_Piers')):before[col.name]=col.hide_render;col.hide_render=True
views=[('ground_all_overview',(5650,925,12000),(5650,925,0),11000,2400,650),('ground_zhonglin_plan',(1225,730,700),(1225,730,0),450,1800,1000),('ground_east_plan',(8900,1190,1400),(8900,1190,0),1900,1800,700),('ground_crossing_detail',(1210,684,40),(1210,715,0),70,1600,1000)]
sc.camera=cam;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.render.image_settings.file_format='PNG'
try:
 for name,pos,target,scale,w,h in views:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;cam.data.clip_end=30000;sc.render.resolution_x=w;sc.render.resolution_y=h;sc.render.resolution_percentage=100;sc.render.filepath=str(root/(name+'.png'));bpy.ops.render.render(write_still=True)
finally:
 for name,state in before.items():bpy.data.collections[name].hide_render=state
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={'file':bpy.data.filepath,'renders':[str(root/(v[0]+'.png')) for v in views],'elevated_render_visibility_restored':True};(root/'render_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
