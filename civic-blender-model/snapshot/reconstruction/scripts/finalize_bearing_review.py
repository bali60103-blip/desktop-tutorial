"""Keep no-fit caps at original geometry, flag partial intersections and render readable detail."""
import bpy,json,pathlib
from mathutils import Vector
root=pathlib.Path(ROOT);p=json.loads((root/'bearing_check.json').read_text());main=bpy.context.scene
red=bpy.data.materials.get('BEARING_UNRESOLVED') or bpy.data.materials.new('BEARING_UNRESOLVED');red.diffuse_color=(.85,.15,.12,1)
for name in p['caps_without_stacks']:
 original=bpy.data.objects[name];o=bpy.data.objects['LOWERED_'+name];vs=[original.matrix_world@v.co for v in original.data.vertices]
 for dst,src in zip(o.data.vertices,vs):dst.co=src
 o.data.materials.clear();o.data.materials.append(red);o['top_delta_m']=0;o['status']='NO FIT: original cap geometry retained, no unsupported lowering applied'
 for r in p['caps']:
  if r['cap']==name:r['comparison_top_z']=r['original_top_z'];r['status']='No-fit original restored'
for r in p['unfitted_intersections']:
 o=bpy.data.objects['LOWERED_'+r['cap']];o['partial_intersections_unresolved']=True
p['lowered_caps']=len(p['caps'])-len(p['caps_without_stacks']);p['no_fit_caps_original_restored']=p['caps_without_stacks'];p['unfitted_intersection_count']=len(p['unfitted_intersections'])
focus=min(p['bearings'],key=lambda q:(q['xy'][0]-1197)**2+(q['xy'][1]-733)**2);scene=bpy.data.scenes.new('BEARING_READABLE_DETAIL');scene.world=main.world;col=bpy.data.collections['BEARING_OPTION_CAP_MINUS_020']
for o in col.objects:
 if focus['cap'] in o.name:scene.collection.objects.link(o)
for name in [focus['girder'],focus['girder'].replace('_bottom','_web'),focus['girder'].replace('_bottom','_top')]:
 if name in bpy.data.objects:scene.collection.objects.link(bpy.data.objects[name])
x,y=focus['xy'];camd=bpy.data.cameras.new('BEARING_READABLE_CAMERA');cam=bpy.data.objects.new(camd.name,camd);scene.collection.objects.link(cam);scene.camera=cam;cam.location=(x+1.5,y-2,5.55);cam.rotation_euler=(Vector((x,y,5.5))-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=2.5;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.filepath=str(root/'bearing_closeup.png');bpy.ops.render.render(write_still=True,scene=scene.name)
scene['purpose']='Isolated modeled bearing connection, nearby structure hidden for inspection. Not a site photo.'
bpy.context.window.scene=main;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);p['file']=bpy.data.filepath;(root/'bearing_check.json').write_text(json.dumps(p,ensure_ascii=False,indent=2));result={'file':p['file'],'lowered_caps':p['lowered_caps'],'bearing_stacks':p['bearing_stacks'],'restored_no_fit_caps':len(p['caps_without_stacks']),'unfitted_intersections':len(p['unfitted_intersections'])}
