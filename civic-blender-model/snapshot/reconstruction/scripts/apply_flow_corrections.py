import bpy,json,pathlib
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Calibration');r=json.load(open(root/'flow_corrections.json'));sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];keep=bpy.data.collections.new('CALIBRATION_RETAINED_CONFLICT_OBJECTS');sc.collection.children.link(keep);removed=[]
for name in r['remove_estimated_columns']+[r['replace_partition']]:
 o=bpy.data.objects[name];keep.objects.link(o)
 for c in list(o.users_collection):
  if c.name in ['COMPLETION_PARKING','COMPLETION_MALLS']:c.objects.unlink(o)
 o['calibration_conflict']=r['status'];removed.append(name)
for p in r['parts']:
 org=Vector(p['mesh']['vertices'][0]);m=bpy.data.meshes.new(p['name']);m.from_pydata([tuple(Vector(v)-org) for v in p['mesh']['vertices']],[],p['mesh']['faces']);m.update();o=bpy.data.objects.new(p['name'],m);o.location=org;bpy.data.collections['COMPLETION_MALLS'].objects.link(o)
sc.view_layers[0].update();sc.view_layers[0].layer_collection.children[keep.name].exclude=True;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);(root/'flow_corrections_applied.json').write_text(json.dumps({'retained_in_excluded_collection':removed,'collection':keep.name,'status':r['status']},ensure_ascii=False,indent=2));result={'retained_objects':len(removed),'file':bpy.data.filepath}
