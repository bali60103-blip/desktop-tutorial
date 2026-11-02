import bpy,json,pathlib,datetime,shutil
from mathutils import Matrix,Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Y26Orientation';out.mkdir(exist_ok=True)
for n in ['orientation.json','osm_context.json']:shutil.copy2('/tmp/civic-y26-context/'+n,out/n)
p=json.load(open(out/'orientation.json'));main=bpy.data.scenes['Scene'];old=bpy.data.collections['Y26_PHOTO_CONFIGURATION_ESTIMATED'];stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_orientation_'+stamp+'.blend')),copy=True)
assert not bpy.data.collections.get('Y26_BUILDING_AXIS_ALTERNATIVE');col=bpy.data.collections.new('Y26_BUILDING_AXIS_ALTERNATIVE');main.collection.children.link(col);main.view_layers[0].layer_collection.children[col.name].exclude=True;anchor=Vector((*p['anchor_live_xy'],0));xf=Matrix.Translation(anchor)@Matrix.Rotation(p['rotation_radians'],4,'Z')@Matrix.Translation(-anchor);count=0
for o in old.objects:
 if o.hide_viewport:continue
 c=o.copy();c.name=o.name+'_AXIS_ALT';col.objects.link(c);c.matrix_world=xf@o.matrix_world;c['orientation_basis']=p['status'];count+=1
sc=bpy.data.scenes.new('Y26_ORIENTATION_COMPARISON');sc.collection.children.link(col);sc.world=main.world;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True
# Reuse existing review camera; no extra camera object.
cam=bpy.data.objects['Y26_PHOTO_REVIEW'];sc.collection.objects.link(cam);sc.camera=cam;prior=cam.matrix_world.copy();scale=cam.data.ortho_scale
cu=bpy.data.curves.new('REFERENCE_BUILDING_FOOTPRINT_OSM381952589','CURVE');cu.dimensions='3D';cu.bevel_depth=.15;sp=cu.splines.new('POLY');sp.points.add(len(p['reference_building_live_xy'])-1)
for v,q in zip(sp.points,p['reference_building_live_xy']):v.co=(*q,0,1)
o=bpy.data.objects.new(cu.name,cu);sc.collection.objects.link(o);o['status']='OSM footprint only; no building height asserted'
center=Vector((100,924,0));cam.location=center+Vector((0,0,100));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=85;sc.render.resolution_x=1400;sc.render.resolution_y=1000;sc.render.resolution_percentage=100;sc.render.filepath=str(out/'Y26_building_axis_plan.png');bpy.ops.render.render(write_still=True,scene=sc.name)
cam.matrix_world=prior;cam.data.ortho_scale=scale
file=out/('CIVIC_Y26_ORIENTATION_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'copied_objects':count,'source_orientation_preserved':True,'new_camera_objects':0,**p};(out/'orientation_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
