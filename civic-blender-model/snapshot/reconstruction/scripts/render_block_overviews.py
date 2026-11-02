import bpy,json,pathlib
from mathutils import Vector
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];cam=bpy.data.objects['FRONTAGE_HEIGHT_CAMERA'];oldmatrix=cam.matrix_world.copy();oldtype=cam.data.type;oldscale=cam.data.ortho_scale;oldclip=cam.data.clip_end;oldcam=sc.camera;oldres=(sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage);oldpath=sc.render.filepath;oldengine=sc.render.engine
r=json.load(open(out/'final_model_check.json'));mn,mx=r['bounds'];views=[('全段街廓',Vector(((mn[0]+mx[0])/2,(mn[1]+mx[1])/2,0)),(mx[0]-mn[0])*1.1,(2400,900))]
for label,oid,scale in [('中林街廓近景','w238509494',500),('臺北文創分部近景','w229059792',420),('松山街廓近景','w298601636',650)]:
 o=bpy.data.objects.get('BLOCK_'+oid+'_CORE')
 if o:
  vs=[o.matrix_world@Vector(v) for v in o.bound_box];c=Vector((sum(v.x for v in vs)/8,sum(v.y for v in vs)/8,0))
 else:c=Vector((1200,760,0))
 views.append((label,c,scale,(1400,1000)))
results=[]
try:
 sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=True;sc.render.image_settings.file_format='PNG';cam.data.type='ORTHO';cam.data.clip_end=40000;sc.camera=cam
 for label,c,scale,res in views:
  cam.location=c+Vector((scale*.10,-scale*.60,scale*.62));cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x=res[0];sc.render.resolution_y=res[1];sc.render.resolution_percentage=100;sc.view_layers[0].update();sc.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name);results.append({'label':label,'file':sc.render.filepath})
finally:
 cam.matrix_world=oldmatrix;cam.data.type=oldtype;cam.data.ortho_scale=oldscale;cam.data.clip_end=oldclip;sc.camera=oldcam;sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage=oldres;sc.render.filepath=oldpath;sc.render.engine=oldengine;sc.view_layers[0].update()
(out/'overview_renders.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));result={'views':results}
