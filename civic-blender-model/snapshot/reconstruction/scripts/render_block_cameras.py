"""Per-camera model views and metadata. External street imagery availability is tracked separately."""
import bpy,json,pathlib,math,time
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');out=root/'camera_renders';out.mkdir(exist_ok=True);sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];cams=sorted([o for o in sc.objects if o.type=='CAMERA' and o.name not in ['FRONTAGE_HEIGHT_CAMERA','BLOCK_FACADE_REVIEW_CAMERA','BLOCK_OVERVIEW_CAMERA']],key=lambda o:o.name);start=CAL_START;end=CAL_END
oldcam=sc.camera;oldengine=sc.render.engine;oldx=sc.render.resolution_x;oldy=sc.render.resolution_y;oldpercent=sc.render.resolution_percentage;oldpath=sc.render.filepath;oldtransparent=sc.render.film_transparent
rows=[]
try:
 sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=640;sc.render.resolution_y=360;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False;sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.background_type='WORLD';sc.world.color=(.15,.18,.22)
 for o in cams[start:end]:
  sc.camera=o;sc.view_layers[0].update();p=out/(o.name+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name);rows.append({'name':o.name,'file':str(p),'location':list(o.location),'rotation_euler':list(o.rotation_euler),'lens_mm':o.data.lens,'sensor_width_mm':o.data.sensor_width,'horizontal_fov_deg':math.degrees(2*math.atan(o.data.sensor_width/(2*o.data.lens))),'scope':'Model visual review only; streetview comparison not completed when imagery unavailable'})
finally:
 sc.camera=oldcam;sc.render.engine=oldengine;sc.render.resolution_x=oldx;sc.render.resolution_y=oldy;sc.render.resolution_percentage=oldpercent;sc.render.filepath=oldpath;sc.render.film_transparent=oldtransparent
(root/('camera_batch_'+str(start)+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2));result={'start':start,'end':end,'rendered':len(rows),'total':len(cams)}
