import bpy,json,pathlib,os,math
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];payload=json.load(open(out/'legacy_slab_trim_payload.json'));bpy.ops.wm.save_as_mainfile(filepath=str(out/'BEFORE_LEGACY_SLAB_TRIM.blend'),copy=True)
keep=bpy.data.collections.new('CAL3_RETAINED_LEGACY_SLABS');sc.collection.children.link(keep);col=bpy.data.collections.new('CAL3_TRIMMED_LEGACY_SLABS');sc.collection.children.link(col);report=[]
for r in payload:
 old=bpy.data.objects[r['source']];keep.objects.link(old)
 for c in list(old.users_collection):
  if c!=keep:c.objects.unlink(old)
 origin=Vector(r['vertices'][0]);m=bpy.data.meshes.new('TRIMMED_'+r['source']);m.from_pydata([tuple(Vector(v)-origin) for v in r['vertices']],[],r['faces']);m.update()
 for mat in old.data.materials:m.materials.append(mat)
 o=bpy.data.objects.new('TRIMMED_'+r['source'],m);o.location=origin;col.objects.link(o);o['source_object']=old.name;o['status']='Legacy overlap trimmed against working floor; source preserved. Heights remain estimated.';report.append({k:v for k,v in r.items() if k not in ['vertices','faces']})
sc.view_layers[0].layer_collection.children[keep.name].exclude=True;sc.view_layers[0].update();oldcam=sc.camera;sc.camera=bpy.data.objects['\u4e2d\u6797_B1_B2_CAMERA'];sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100;sc.render.filepath=str(out/'ZHONGLIN_SLAB_TRIM_REVIEW.png');bpy.ops.render.render(write_still=True,scene=sc.name);sc.camera=oldcam;(out/'legacy_slab_trim_report.json').write_text(json.dumps({'changes':report,'unresolved':'Ramp surfaces and road markings may still overlap; Dunyan/Yanji overlap deliberately retained. This only removes legacy floor duplication.'},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_PHOTO_CALIBRATION_20260911.blend'));result={'trimmed':len(report),'originals_retained':len(keep.objects)}
