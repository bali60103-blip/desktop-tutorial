import bpy,json,os,pathlib,datetime
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;r=json.load(open(out/'southwest_plant_photo_payload.json'));name='SOUTHWEST_PLANT_PHOTO_0912_EST';assert not bpy.data.collections.get(name),'Already built';report=json.load(open(out/'mapped_vent_shell_report.json'));oldname=next(x['new_object'] for x in report['items'] if x['osm_id']==r['osm_id']);old=sc.objects[oldname]
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_SOUTHWEST_PLANT_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
# Clone only main-scene collection membership; earlier scenes keep the old shaft.
for col in list(sc.collection.children):
 if old.name not in col.objects:continue
 state=sc.view_layers[0].layer_collection.children[col.name].exclude;clone=col.copy();clone.name='SWPLANT12_'+col.name;sc.collection.children.unlink(col);sc.collection.children.link(clone);clone.objects.unlink(old);sc.view_layers[0].layer_collection.children[clone.name].exclude=state
col=bpy.data.collections.new(name);sc.collection.children.link(col);materials={}
for key,color in {'STONE':(.49,.51,.52,1),'LATTICE':(.38,.12,.08,1),'FAN':(.75,.76,.73,1),'METAL':(.06,.075,.08,1),'JOINT':(.13,.14,.15,1)}.items():
 m=bpy.data.materials.new('SWPLANT_'+key);m.diffuse_color=color;materials[key]=m
objects=[]
for row in r['pieces']:
 origin=Vector(row['vertices'][0]);m=bpy.data.meshes.new('SWPLANT_'+row['name']);m.from_pydata([Vector(v)-origin for v in row['vertices']],[],row['faces']);m.materials.append(materials[row['material']]);m.update();o=bpy.data.objects.new(m.name,m);col.objects.link(o);o.location=origin;o['osm_id']=r['osm_id'];o['status']='Photo-informed estimate; 2025 imagery; unmeasured dimensions and rear elevations';o['source_url']=r['source_url'];objects.append(o.name)
sc.view_layers[0].update();assert not old.visible_get();assert all(sc.objects[n].visible_get() for n in objects)
report={k:v for k,v in r.items() if k!='pieces'};report.update({'retained_object':old.name,'objects':objects,'parts':len(objects),'main_scene_replacement':True});(out/'southwest_plant_photo_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
# Dedicated three-view inspection, independent of the animated route.
review=bpy.data.scenes.new('SOUTHWEST_PLANT_REVIEW_0912');review.use_fake_user=True;review.collection.children.link(col);review.render.engine='BLENDER_WORKBENCH';review.render.resolution_x=1000;review.render.resolution_y=700;review.render.resolution_percentage=100;review.display.shading.light='STUDIO';review.display.shading.color_type='MATERIAL';review.display.shading.show_shadows=False;review.display.shading.show_cavity=True;review.display.shading.background_type='WORLD';review.world=bpy.data.worlds.new('SOUTHWEST_PLANT_REVIEW_WORLD');review.world.color=(.07,.07,.07)
cd=bpy.data.cameras.new('SOUTHWEST_PLANT_REVIEW_CAMERA');cam=bpy.data.objects.new(cd.name,cd);review.collection.objects.link(cam);review.camera=cam;cd.type='ORTHO';cd.ortho_scale=28;cd.clip_end=500
for label,pos,target in [('WEST',(509,595,11),(553,608,2.4)),('SW',(513,564,23),(553,608,2.4)),('NORTH',(553,652,17),(553,608,2.4))]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();review.render.filepath=str(out/('SOUTHWEST_PLANT_'+label+'.png'));bpy.ops.render.render(write_still=True,scene=review.name)
bpy.context.window.scene=sc;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_FULL_CORRIDOR_WORKING_20260912.blend'));result={'parts':len(objects),'prior_height':r['prior_height_m'],'estimated_heights':r['total_height_estimate_m'],'rendered':3,'old_preserved':old.name}
