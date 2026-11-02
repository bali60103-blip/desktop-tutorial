"""Inside Blender: save live edits, make a separate review version and render workbench QA.
ROOT supplied externally. Never marks an incomplete gate passed.
"""
import bpy,pathlib,json,datetime
from mathutils import Vector
root=pathlib.Path(ROOT);root.mkdir(parents=True,exist_ok=True);stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');sc=bpy.context.scene
prior=bpy.data.filepath
snapshot=root/('B_IN_PROGRESS_before_review_'+stamp+'.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(snapshot),copy=True)
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1600;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.background_type='WORLD';sc.world.color=(.8,.8,.8)
col=bpy.data.collections.get('GATE_REVIEW_CAMERAS')
if col is None:col=bpy.data.collections.new('GATE_REVIEW_CAMERAS');sc.collection.children.link(col)
views=[('B_full_plan',(2464.6,677.5,7000),(2464.6,677.5,0),6800),('B_zhonglin_plan',(1225,735,900),(1225,735,0),560),('B_zhonglin_oblique',(1225,370,290),(1225,735,0),590)]
items=[]
for name,pos,target,scale in views:
 ob=bpy.data.objects.get('REVIEW_'+name)
 if ob is None:
  data=bpy.data.cameras.new('REVIEW_'+name);ob=bpy.data.objects.new(data.name,data);col.objects.link(ob)
 ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();ob.data.type='ORTHO';ob.data.ortho_scale=scale;ob.data.clip_end=20000
 items.append({'name':name,'camera':ob.name,'output':str(root/(name+'.png'))})
sc.camera=bpy.data.objects[items[0]['camera']]
sc['GATE_REVIEW_STATUS']='B IN PROGRESS: renders show work model, not verified as-built; C/D/E not passed'
output=root/('B_review_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(output))
result={'snapshot':str(snapshot),'review_file':str(output),'prior_file':prior,'gate_status':{'A':'scope accepted','B':'IN PROGRESS','C':'not passed','D':'not passed','E':'not passed'},'views':items,'limitations':['Work-model dimensions include estimates','Legacy piers unverified','Underground reference outlines do not establish floor elevations','Rendering is not validation of geographic accuracy']}
(root/'review_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
