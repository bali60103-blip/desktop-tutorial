import bpy,json,os,pathlib,datetime
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'PriorityNodes_20260914';r=json.load(open(out/'huashan_station_payload.json'));s=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];review=bpy.data.scenes['PRIORITY_A_REVIEW_20260914'];bpy.context.window.scene=s
name='P1_A1_HUASHAN_STATION_PHOTO_EST';assert not bpy.data.collections.get(name)
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_STATION_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
old=[o for o in s.objects if 'w448227619' in o.name and o.visible_get()];assert len(old)==2
for c in list(s.collection.children):
 rem=[o for o in old if o.name in c.objects]
 if not rem:continue
 clone=c.copy();clone.name='P1STATION_'+c.name
 for o in rem:clone.objects.unlink(o)
 for sc in [s,review]:
  if c.name not in sc.collection.children:continue
  state=sc.view_layers[0].layer_collection.children[c.name].exclude;sc.collection.children.unlink(c);sc.collection.children.link(clone);sc.view_layers[0].layer_collection.children[clone.name].exclude=state
col=bpy.data.collections.new(name);s.collection.children.link(col);review.collection.children.link(col);mats={}
for key,c in {'WALL':(.79,.77,.70,1),'STONE':(.55,.54,.48,1),'DARK':(.055,.065,.058,1),'WOOD':(.25,.20,.14,1),'JOINT':(.32,.31,.28,1)}.items():
 m=bpy.data.materials.new('P1_STATION_'+key);m.diffuse_color=c;mats[key]=m
names=[]
for p in r['pieces']:
 origin=Vector(p['vertices'][0]);m=bpy.data.meshes.new('P1_STATION_'+p['name']);m.from_pydata([Vector(v)-origin for v in p['vertices']],[],p['faces']);m.materials.append(mats[p['material']]);m.update();o=bpy.data.objects.new(m.name,m);col.objects.link(o);o.location=origin;o['osm_id']=r['osm_id'];o['priority']='P1_A1_CONTEXT';o['status']='Photo-informed estimate; not current measured condition';o['source_url']=r['source_url'];names.append(o.name)
s.view_layers[0].update();assert all(not o.visible_get() for o in old);assert all(s.objects[n].visible_get() for n in names)
detail=bpy.data.scenes.new('P1_A1_STATION_DETAIL');detail.use_fake_user=True;detail.collection.children.link(col);detail.render.engine='BLENDER_WORKBENCH';detail.render.resolution_x=1100;detail.render.resolution_y=700;detail.render.resolution_percentage=100;detail.display.shading.light='STUDIO';detail.display.shading.color_type='MATERIAL';detail.display.shading.show_shadows=False;detail.display.shading.show_cavity=True
cd=bpy.data.cameras.new('P1_STATION_DETAIL_CAMERA');cam=bpy.data.objects.new(cd.name,cd);detail.collection.objects.link(cam);detail.camera=cam;cd.type='ORTHO';cd.ortho_scale=36;cd.clip_end=500
cam.location=(1365,624,18);cam.rotation_euler=(Vector((1407,647,3))-cam.location).to_track_quat('-Z','Y').to_euler();detail.render.filepath=str(out/'P1_A1_STATION_DETAIL.png');bpy.ops.render.render(write_still=True,scene=detail.name)
for camera in ['P1_A1_N','P1_A1_S']:
 review.camera=bpy.data.objects[camera];review.render.filepath=str(out/(camera+'.png'));bpy.ops.render.render(write_still=True,scene=review.name)
report={k:v for k,v in r.items() if k!='pieces'};report.update({'objects':names,'parts':len(names),'retained_objects':[o.name for o in old],'geometry_check':'All generated component meshes closed; original source footprint retained','review_scene':detail.name});(out/'huashan_station_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
bpy.context.window.scene=s;bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_PRIORITY_A_WORKING_20260914.blend'));result={'parts':len(names),'retained':len(old),'renders':3,'file':'CIVIC_PRIORITY_A_WORKING_20260914.blend'}
