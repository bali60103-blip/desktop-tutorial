import bpy,json,pathlib,re,time
from mathutils import Vector
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Calibration');sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];r=json.load(open(out/'secondary_corrections.json'));bpy.ops.wm.save_as_mainfile(filepath=str(out/'BEFORE_HEADROOM_CORRECTIONS.blend'),copy=True);keep=bpy.data.collections['CALIBRATION_RETAINED_CONFLICT_OBJECTS'];reports=[]
for name in {p['replaces'] for p in r['parts']}:
 old=bpy.data.objects[name];dest=next(c for c in old.users_collection if c.name in ['COMPLETION_GROUND_HIGHWAY','COMPLETION_REMOVABLE_ROOFS']);ps=[p for p in r['parts'] if p['replaces']==name]
 for p in ps:
  vs=p['mesh']['vertices'];org=Vector(vs[0]);m=bpy.data.meshes.new(p['name']);m.from_pydata([tuple(Vector(v)-org) for v in vs],[],p['mesh']['faces']);m.update();o=bpy.data.objects.new(p['name'],m);o.location=org;dest.objects.link(o)
  for mat in old.data.materials:m.materials.append(mat)
  o['calibration_status']='Provisional access-consistent cut; actual location still unverified';o['replaces']=name
 if old.name not in keep.objects:keep.objects.link(old)
 dest.objects.unlink(old)
steps=[]
for o in list(sc.objects):
 if o.type!='MESH' or not re.search(r'^COMP_.*_CORE\d+_L\d+_[AB]\d+$',o.name):continue
 oldmesh=o.data;vs=[o.matrix_world@v.co for v in oldmesh.vertices];z0=min(v.z for v in vs);z1=max(v.z for v in vs);oldmesh.use_fake_user=True;o.data=oldmesh.copy();inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  w=o.matrix_world@v.co
  if abs(w.z-z0)<1e-4:w.z=z1-.2;v.co=inv@w
 o.data.update();o['calibration_status']='Estimated0.20m tread thickness replaces full-depth fill obstructing lower flight; not structural design';steps.append(o.name)
# Previous Zhonglin ramp samples remain in source scenes; remove overlapping old alternatives from combined assembly.
duplicates=[];ground=bpy.data.collections['COMPLETION_GROUND_HIGHWAY']
for o in list(ground.objects):
 if o.name.startswith(('EAST_0_TO_B1_ASSUMED','WEST_0_TO_B1_ASSUMED')):
  if o.name not in keep.objects:keep.objects.link(o)
  ground.objects.unlink(o);duplicates.append(o.name)
sc.view_layers[0].update();sc.view_layers[0].layer_collection.children[keep.name].exclude=True;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);report={'treads_repaired':len(steps),'tread_objects':steps,'old_ramp_alternatives_retained':duplicates,'secondary_surfaces':r['reports'],'new_objects':len(r['parts']),'file':bpy.data.filepath};(out/'secondary_applied.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));result={k:v for k,v in report.items() if k not in ['tread_objects','old_ramp_alternatives_retained']};result['old_ramp_objects_retained']=len(duplicates)
