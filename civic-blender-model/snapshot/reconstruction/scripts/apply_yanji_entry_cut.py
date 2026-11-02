import bpy,json,pathlib
from mathutils import Vector
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/CalibrationRound2');sc=bpy.context.scene
assert sc.name=='CIVIC_BLOCKS_FACADES_WORKING'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'BEFORE_ROUND2.blend'),copy=True)
r=json.load(open(out/'yanji_entry_cut.json'));old=bpy.data.objects[r['source_object']];source=bpy.data.collections['COMPLETION_PARKING'];assert source.name in sc.collection.children
new=bpy.data.collections.new('CAL_ROUND2_PARKING');sc.collection.children.link(new)
for o in source.objects:
 if o!=old:new.objects.link(o)
sc.collection.children.unlink(source)
created=[]
for i,m in enumerate(r['parts']):
 org=Vector(m['vertices'][0]);me=bpy.data.meshes.new('YANJI_ENTRY_WALL_'+str(i));me.from_pydata([tuple(Vector(v)-org) for v in m['vertices']],[],m['faces']);me.update();o=bpy.data.objects.new('CAL2_YANJI_ENTRY_WALL_'+str(i),me);o.location=org;new.objects.link(o)
 for mat in old.data.materials:me.materials.append(mat)
 o['verification_status']=r['status'];o['source_object']=old.name;o['opening_width_assumed_m']=r['opening_width_m'];created.append(o.name)
sc['round2_status']='Yanji B1-only confirmed; assumed entry-wall conflict corrected; remaining overlap and absolute positions unresolved.'
sc.view_layers[0].update();fp=out/'CIVIC_CALIBRATION_ROUND2_20260911.blend';bpy.ops.wm.save_as_mainfile(filepath=str(fp))
result={'file':str(fp),'new_objects':created,'original_scene_wall_preserved':old.name in bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'].objects,'status':r['status']};(out/'applied.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
