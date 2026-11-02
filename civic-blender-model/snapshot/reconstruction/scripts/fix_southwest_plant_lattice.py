import bpy,json,os,pathlib,datetime
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;r=json.load(open(out/'southwest_plant_photo_payload.json'));col=bpy.data.collections['SOUTHWEST_PLANT_PHOTO_0912_EST'];bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_LATTICE_FIX_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True);names=[]
for row in r['pieces']:
 name='SWPLANT_'+row['name'];o=col.objects.get(name);origin=Vector(row['vertices'][0]);me=bpy.data.meshes.new(name+'_COMPLETE_GRID');me.from_pydata([Vector(v)-origin for v in row['vertices']],[],row['faces']);me.materials.append(bpy.data.materials['SWPLANT_'+row['material']]);me.update()
 if o:o.data.use_fake_user=True;o.data=me
 else:o=bpy.data.objects.new(name,me);col.objects.link(o)
 o.location=origin;o['osm_id']=r['osm_id'];o['source_url']=r['source_url'];o['status']='Photo-informed estimate, 2025 imagery; unmeasured dimensions and rear elevations';names.append(o.name)
report=json.load(open(out/'southwest_plant_photo_report.json'));report['objects']=names;report['parts']=len(names);report['lattice_corrected']='Extended both diagonal families across complete aperture; prototype coverage repair';(out/'southwest_plant_photo_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));review=bpy.data.scenes['SOUTHWEST_PLANT_REVIEW_0912'];cam=review.camera
for label,pos,target in [('WEST',(509,595,11),(553,608,2.4)),('SW',(513,564,23),(553,608,2.4)),('NORTH',(553,652,17),(553,608,2.4))]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();review.render.filepath=str(out/('SOUTHWEST_PLANT_'+label+'.png'));bpy.ops.render.render(write_still=True,scene=review.name)
bpy.context.window.scene=sc;bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_FULL_CORRIDOR_WORKING_20260912.blend'));result={'parts':len(names),'lattice_complete':True}
