import bpy,json,pathlib,shutil
from mathutils import Vector
P=pathlib.Path('/tmp/civic-rebuild');root=pathlib.Path((P/'output_root.txt').read_text());scene=bpy.context.scene
new=bpy.data.collections.new('13_Median_gap_inference');bpy.data.collections['CIVIC_REBUILD__METERS__SOURCE_TAGGED'].children.link(new)
m=bpy.data.materials.new('Median_inferred_ochre');m.diffuse_color=(.57,.43,.23,1);m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=m.diffuse_color
for r in json.loads((P/'supplement_payload.json').read_text()):
 me=bpy.data.meshes.new(r['name']);me.from_pydata(r['vertices'],[],r['faces']);me.materials.append(m);o=bpy.data.objects.new(r['name'],me);new.objects.link(o)
 for k,v in r['props'].items():o[k]=v
cam=bpy.data.objects['CAM_02_Jinshan_detail'];cam.location=(2440,290,65);target=Vector((2350,435,4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=190
scene.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
scene.render.filepath=str(root/'preview_detail.png');bpy.ops.render.render(write_still=True)
# Separate technical cutaway, with context hidden only for this render.
context=bpy.data.collections['10_Buildings_context'];context.hide_render=True
cam.location=(2400,350,24);target=Vector((2350,433,4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=130
scene.render.filepath=str(root/'preview_structure_ESTIMATED.png');bpy.ops.render.render(write_still=True)
context.hide_render=False
cam.location=(2440,290,65);target=Vector((2350,435,4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=190
scene.camera=bpy.data.objects['CAM_01_Full_corridor'];scene.render.filepath=str(root/'preview_overview.png');bpy.ops.render.render(write_still=True)
scene.camera=cam;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'saved':bpy.data.filepath,'previews':3}
