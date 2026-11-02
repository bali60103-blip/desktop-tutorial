import bpy,json,pathlib,collections,math
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];sc.view_layers[0].update();bad=[];count=0;vertices=faces=0
for o in sc.objects:
 if o.type!='MESH' or not o.name.startswith('COMP_'):continue
 count+=1;m=o.data;vertices+=len(m.vertices);faces+=len(m.polygons);ec=collections.Counter(tuple(sorted(e)) for p in m.polygons for e in p.edge_keys);z=sum(p.area<1e-10 for p in m.polygons);nf=sum(not all(math.isfinite(x) for x in v.co) for v in m.vertices);edges=sum(n!=2 for n in ec.values())
 if z or nf or edges:bad.append({'object':o.name,'zero_area_faces':z,'nonfinite_vertices':nf,'nonmanifold_edges':edges})
# Preserve camera transforms and render a full corridor frame with margins from frontage bounds.
cam=bpy.data.objects['FRONTAGE_HEIGHT_CAMERA'];old=cam.matrix_world.copy();scale=cam.data.ortho_scale;clip=cam.data.clip_end;verts=[o.matrix_world@Vector(v) for o in bpy.data.collections['COMPLETION_FRONTAGE'].objects if o.type=='MESH' for v in o.bound_box];minx=min(v.x for v in verts);maxx=max(v.x for v in verts);miny=min(v.y for v in verts);maxy=max(v.y for v in verts);center=Vector(((minx+maxx)/2,(miny+maxy)/2,0))
try:
 cam.location=center+Vector((0,-9000,9000));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=maxx-minx+1800;cam.data.clip_end=50000;sc.camera=cam;sc.view_layers[0].update();sc.render.filepath=str(out/'全段.png');bpy.ops.render.render(write_still=True,scene=sc.name)
finally:cam.matrix_world=old;cam.data.ortho_scale=scale;cam.data.clip_end=clip;sc.view_layers[0].update()
# Add prior unresolved findings explicitly to deferred issues text.
issues=json.load(open(out/'all_deferred_issues.json'))
prior=[{'id':'PRIOR_BOOLEAN_TOPOLOGY','type':'known_nonmanifold','detail':'Road3+median2 evaluated Boolean edges; prior Validation/final_validation_check.json'}, {'id':'PRIOR_BEARINGS','type':'unfitted_supports','detail':'577/680/681 no fitted bearings;114 candidate cap/girder intersections unresolved'}, {'id':'PRIOR_VERTICAL_DATUM','type':'estimated_elevation','detail':'B1/B2=-3.6/-7.2 and mall clearheight2.8 are assumed; no survey datum'}, {'id':'PRIOR_Y26_ORIENTATION','type':'alternative_heading','detail':'A/B remain alternative scenes; assembly uses mapped straight working entrances'}, {'id':'PRIOR_ALL_PATH_CLEARANCE','type':'not_checked','detail':'New estimated interiors/access routes not full swept-body or car-clearance checked'}]
for r in prior:
 if not any(i['id']==r['id'] for i in issues):issues.append(r)
(out/'all_deferred_issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2));t=bpy.data.texts['CIVIC_DEFERRED_ISSUES.json'];t.clear();t.write(json.dumps(issues,ensure_ascii=False,indent=2))
for ar in bpy.context.screen.areas:
 if ar.type=='VIEW_3D':ar.spaces.active.clip_end=30000;ar.spaces.active.region_3d.view_location=center;ar.spaces.active.region_3d.view_distance=(maxx-minx)*.85
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
r={'file':bpy.data.filepath,'new_active_meshes':count,'new_active_vertices':vertices,'new_active_faces':faces,'mesh_issues':bad,'deferred_issues':len(issues),'route_cameras_in_assembly':sum(o.type=='CAMERA' and o.name.startswith('CIVIC200_') for o in sc.objects),'estimated_access_cameras':sum(o.type=='CAMERA' and o.name.startswith('COMP_ACCESS_') for o in sc.objects),'scope':'Finite geometry/zero-area/topology checks only. Overlaps, estimated layouts and site calibration deferred.'};(out/'checkpoint_mesh_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
