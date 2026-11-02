import bpy,pathlib,json,collections,shutil
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Validation'
p=json.load(open(root/'Y26Orientation/integrated_clearance_payload.json'));keep={m['name'] for m in p['parts']};archived=[]
for o in bpy.data.scenes['Y26_B_INTEGRATED_COMPARISON'].objects:
 if o.name.startswith('Y26_B_INTEGRATED_WALL_') and o.name not in keep:
  o.hide_render=True;o.hide_viewport=True;o['status']='ARCHIVED pre-clearance wall; retained for comparison';archived.append(o.name)
for name in ['technical_audit.json','walk_envelope_audit.json']:
 if not (out/('before_'+name)).exists():shutil.copy2(out/name,out/('before_'+name))
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
exec(pathlib.Path('/tmp/civic-stage00/reconstruction/scripts/validate_civic_model.py').read_text())
exec(pathlib.Path('/tmp/civic-stage00/reconstruction/scripts/validate_walk_envelopes.py').read_text())
# Evaluate active Boolean outputs, since raw mesh checks do not cover modifiers.
sc=bpy.data.scenes['Scene'];evaluated=[]
with bpy.context.temp_override(scene=sc,view_layer=sc.view_layers[0]):
 deps=bpy.context.evaluated_depsgraph_get()
 for name in ['GROUND_ROADS_OFFICIAL_XY','GROUND_MEDIAN_WORKING_ESTIMATED']:
  o=bpy.data.objects[name];eo=o.evaluated_get(deps);me=eo.to_mesh();ec=collections.Counter(tuple(sorted(e)) for f in me.polygons for e in f.edge_keys)
  evaluated.append({'object':name,'vertices':len(me.vertices),'faces':len(me.polygons),'boundary_edges':sum(n==1 for n in ec.values()),'multi_face_edges':sum(n>2 for n in ec.values()),'zero_area_faces':sum(p.area<1e-10 for p in me.polygons)});eo.to_mesh_clear()
# Diagnostic cutaway render, restoring all temporary camera/roof settings.
sc=bpy.data.scenes['Y26_B_INTEGRATED_COMPARISON'];cam=sc.camera;old=cam.matrix_world.copy();scale=cam.data.ortho_scale;oldpath=sc.render.filepath;roof=bpy.data.objects['Y26_REMOVABLE_ROOF_AXIS_ALT'];hidden=roof.hide_render
try:
 center=Vector((113,932,-2));cam.location=center+Vector((12,-16,12));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=27;roof.hide_render=True;sc.render.filepath=str(out/'Y26_clearance_verified.png');bpy.ops.render.render(write_still=True,scene=sc.name)
finally:
 cam.matrix_world=old;cam.data.ortho_scale=scale;roof.hide_render=hidden;sc.render.filepath=oldpath
r={'file':bpy.data.filepath,'obsolete_walls_archived':archived,'evaluated_modifier_meshes':evaluated,'render':str(out/'Y26_clearance_verified.png')};(out/'final_validation_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
