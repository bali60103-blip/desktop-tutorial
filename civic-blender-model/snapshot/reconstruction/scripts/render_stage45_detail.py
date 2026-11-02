"""Clear inspection views: temporarily remove bridge occlusion, retain original model state."""
import bpy,pathlib,json,bmesh
from mathutils import Vector
root=pathlib.Path(ROOT);main=bpy.context.scene;section=bpy.data.scenes['STAGE04_B_SELECTED_OPEN_SECTION'];cam=section.camera
cam.location=(1208,660,4);cam.rotation_euler=(Vector((1208,726,-3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=80;section.render.resolution_x=1700;section.render.resolution_y=1000;section.render.filepath=str(root/'selected_depth_detail.png');bpy.ops.render.render(write_still=True,scene=section.name)
scene=bpy.data.scenes['STAGE05_ALTERNATIVE_PIERS_REVIEW'];cam=scene.camera;p=json.loads((root/'pier_alternatives.json').read_text());focus=next(r for r in p['groups'] if r['cap']=='UNVERIFIED_Pier_540_CAP_ESTIMATED');x,y=focus['center_xy'];cam.location=(x,y,100);cam.rotation_euler=(0,0,0);cam.data.ortho_scale=85
cam.rotation_euler=(Vector((x,y,0))-cam.location).to_track_quat('-Z','Y').to_euler()
cols=[bpy.data.collections[n] for n in ['04_Elevated_deck_estimated','05_Parapets_estimated','06_Steel_girders_estimated']];states=[c.hide_render for c in cols];alt=bpy.data.collections['WORKSHEET05_PIER_ALTERNATIVE__ESTIMATED'];mark=bpy.data.collections['WORKSHEET05_SHIFT_MARKERS__REVIEW'];original=bpy.data.collections['07_Piers_legacy_UNVERIFIED']
try:
 for c in cols:c.hide_render=True
 scene.render.filepath=str(root/'pier_alternative_plan.png');bpy.ops.render.render(write_still=True,scene=scene.name)
 scene.collection.children.unlink(alt);scene.collection.children.unlink(mark);scene.collection.children.link(original)
 scene.render.filepath=str(root/'pier_original_plan.png');bpy.ops.render.render(write_still=True,scene=scene.name)
finally:
 if original.name in scene.collection.children:scene.collection.children.unlink(original)
 if alt.name not in scene.collection.children:scene.collection.children.link(alt)
 if mark.name not in scene.collection.children:scene.collection.children.link(mark)
 for c,v in zip(cols,states):c.hide_render=v
checks=[]
for o in bpy.data.collections['WORKSHEET04_B_DEPTH__ASSUMED_PILOT_CELL'].objects:
 if o.type!='MESH':continue
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);bm.to_mesh(o.data);bm.free();checks.append({'object':o.name,'nonmanifold_edges':bad})
# Re-render section after normal correction.
section.render.filepath=str(root/'selected_depth_detail.png');bpy.ops.render.render(write_still=True,scene=section.name)
bpy.context.window.scene=main;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={'file':bpy.data.filepath,'new_mesh_checks':checks,'section_display':'Open test cell, roof/south wall omitted intentionally; not completed parking model'};(root/'detail_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
