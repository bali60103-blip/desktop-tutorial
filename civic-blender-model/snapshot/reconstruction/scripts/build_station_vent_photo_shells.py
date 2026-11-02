import bpy,json,os,pathlib,datetime
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;r=json.load(open(out/'station_vent_photo_payload.json'));name='STATION_VENT_PHOTO_SHELLS_0912_EST';assert not bpy.data.collections.get(name),'Already built';lookup={x['osm_id']:x['new_object'] for x in json.load(open(out/'mapped_vent_shell_report.json'))['items']};old=[sc.objects[lookup[x['osm_id']]] for x in r['items']]
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_STATION_VENTS_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
for col in list(sc.collection.children):
 targets=[o for o in old if o.name in col.objects]
 if not targets:continue
 state=sc.view_layers[0].layer_collection.children[col.name].exclude;clone=col.copy();clone.name='STATION12_'+col.name;sc.collection.children.unlink(col);sc.collection.children.link(clone)
 for o in targets:clone.objects.unlink(o)
 sc.view_layers[0].layer_collection.children[clone.name].exclude=state
col=bpy.data.collections.new(name);sc.collection.children.link(col);mats={}
for key,color in {'STONE':(.50,.52,.53,1),'METAL':(.08,.09,.09,1),'DOOR':(.25,.27,.28,1),'JOINT':(.2,.22,.23,1)}.items():
 m=bpy.data.materials.new('STATION_VENT_'+key);m.diffuse_color=color;mats[key]=m
report=[]
for row in r['items']:
 objs=[]
 for part in row['pieces']:
  origin=Vector(part['vertices'][0]);m=bpy.data.meshes.new('STATION_VENT_'+row['osm_id']+'_'+part['name']);m.from_pydata([Vector(v)-origin for v in part['vertices']],[],part['faces']);m.materials.append(mats[part['material']]);m.update();o=bpy.data.objects.new(m.name,m);col.objects.link(o);o.location=origin;o['osm_id']=row['osm_id'];o['source_url']=r['source_url'];o['status']='2025 group photo informed estimate; dimensions and unobserved faces unverified';o['group_extrapolation']=not row['observed_group_member'];objs.append(o.name)
 report.append({**{k:v for k,v in row.items() if k!='pieces'},'objects':objs,'retained_object':lookup[row['osm_id']]})
sc.view_layers[0].update();assert all(not o.visible_get() for o in old)
report={'items':report,'source_url':r['source_url'],'imagery_date':r['imagery_date'],'scope':r['scope']};(out/'station_vent_photo_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
review=bpy.data.scenes.new('STATION_VENT_PHOTO_REVIEW_0912');review.use_fake_user=True;review.collection.children.link(col);review.render.engine='BLENDER_WORKBENCH';review.render.resolution_x=1200;review.render.resolution_y=800;review.render.resolution_percentage=100;review.display.shading.light='STUDIO';review.display.shading.color_type='MATERIAL';review.display.shading.show_shadows=False;review.display.shading.show_cavity=True
cd=bpy.data.cameras.new('STATION_VENT_REVIEW_CAMERA');cam=bpy.data.objects.new(cd.name,cd);review.collection.objects.link(cam);review.camera=cam;cd.type='ORTHO';cd.ortho_scale=80;cd.clip_end=500
for label,pos,target in [('GROUP',(635,687,45),(559,727,3.6)),('FRONT',(615,725,15),(559,727,3.6))]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();review.render.filepath=str(out/('STATION_VENTS_'+label+'.png'));bpy.ops.render.render(write_still=True,scene=review.name)
bpy.context.window.scene=sc;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_FULL_CORRIDOR_WORKING_20260912.blend'));result={'shafts':len(report['items']),'parts':sum(len(x['objects']) for x in report['items']),'rendered':2,'prior_preserved':True}
