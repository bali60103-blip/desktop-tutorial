"""Apply selected depth to an explicitly assumed pilot cell; render estimated pier alternatives.
User selected -3.6/-7.2m and side-by-side original/alternative piers. No as-built claim.
"""
import bpy,json,pathlib,datetime,math
from mathutils import Vector
root=pathlib.Path(ROOT);main=bpy.context.scene;s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_selected_'+s+'.blend')),copy=True)
for scene_name in ['STAGE05_ALTERNATIVE_PIERS_REVIEW','STAGE04_B_SELECTED_OPEN_SECTION']:
 old_scene=bpy.data.scenes.get(scene_name)
 if old_scene:bpy.data.scenes.remove(old_scene)
p=json.loads((root/'pier_alternatives.json').read_text());audit=json.loads((root.parent/'Stage03_Zhonglin/zhonglin_audit.json').read_text())
def newcol(name):
 c=bpy.data.collections.get(name)
 if c:
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
 c=bpy.data.collections.new(name);main.collection.children.link(c);return c
ug=newcol('WORKSHEET04_B_DEPTH__ASSUMED_PILOT_CELL');alt=newcol('WORKSHEET05_PIER_ALTERNATIVE__ESTIMATED');markers=newcol('WORKSHEET05_SHIFT_MARKERS__REVIEW')
def mat(name,c):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
blue=mat('S45_SelectedDepth',(.13,.4,.63));orange=mat('S45_ShiftAlternative',(.95,.38,.08));gray=mat('S45_Slab',(.55,.6,.65));red=mat('S45_Conflict',(.8,.08,.06))
center=Vector((1208.59026,726.42395,0));ang=math.atan2(721.741783-731.106122,1288.333559-1128.846965);v=Vector((math.cos(ang),math.sin(ang),0));n=Vector((-v.y,v.x,0))
def box(name,loc,dim,material,angle=0,col=ug):
 vs=[(sx*dim[0]/2,sy*dim[1]/2,sz*dim[2]/2) for sx,sy,sz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]);me.materials.append(material);o=bpy.data.objects.new(name,me);col.objects.link(o);o.location=loc;o.rotation_euler.z=angle;o['evidence']='ASSUMED PILOT CELL: 200x24m display envelope, NOT parking footprint';return o
# B1 slab with an explicit 36x3.5m opening for the test B1-B2 ramp.
for name,x,y,dx,dy in [('west',-59,0,82,24),('east',59,0,82,24),('north',0,6.875,36,10.25),('south',0,-6.875,36,10.25)]:
 loc=center+v*x+n*y+Vector((0,0,-3.75));box('B1_SLAB_'+name,loc,(dx,dy,.3),blue,ang)
box('B2_SLAB',center+Vector((0,0,-7.35)),(200,24,.3),blue,ang)
# Keep section open: only north wall and end walls, intentionally no south wall/roof.
box('NORTH_WALL_SECTION',center+n*12+Vector((0,0,-4.05)),(200,.3,6.3),gray,ang)
ramps=[]
def ramp(name,a,b,z0,z1,width):
 a=Vector((*a,z0));b=Vector((*b,z1));t=b-a;run=math.hypot(t.x,t.y);side=Vector((-t.y/run,t.x/run,0))*width/2
 vs=[a-side,a+side,b+side,b-side];vs+= [q-Vector((0,0,.25)) for q in vs]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]);me.materials.append(orange);o=bpy.data.objects.new(name,me);ug.objects.link(o);o['status']='Assumed constant grade, no transition curves, curb or traffic design; source-node role as ramp top unverified';ramps.append({'name':name,'run_m':run,'rise_m':z1-z0,'grade':abs(z1-z0)/run,'width_m':width})
for r in audit['routes']:
 if r['osm_id']=='313684462':ramp('WEST_0_TO_B1_ASSUMED',r['live_xy'][0],r['live_xy'][-1],0,-3.6,3.5)
 if r['osm_id']=='313684460':ramp('EAST_0_TO_B1_ASSUMED',r['live_xy'][-1],r['live_xy'][0],0,-3.6,3.5)
a=center-v*18;b=center+v*18;ramp('B1_TO_B2_TEST_RAMP',a[:2],b[:2],-3.6,-7.2,3.5)
ug['selected_depth']='B1=-3.6m; B2=-7.2m; user-selected assumption';ug['scope']='200x24m partial test cell; not registered building perimeter; open section, no roof. Four actual stairs unlocated.'
# Clone active bents into alternate collection, shift whole group; originals untouched.
for group in p['groups']:
 d=group['selected_for_comparison'];delta=Vector((*d['delta_xy'],0)) if d else Vector((0,0,0))
 for name in group['piers']+[group['cap']]:
  src=bpy.data.objects.get(name)
  if src is None:continue
  o=src.copy();o.data=src.data.copy();alt.objects.link(o);o.name='ALT_'+name;o.location+=delta;o.hide_render=False;o.hide_set(False);o['status']='Estimated alternative; not as-built. Structural redesign and foundation checks unresolved.'
  if d:o.data.materials.clear();o.data.materials.append(orange)
  elif group['original_overlap_m2']>.01:o.data.materials.clear();o.data.materials.append(red);o['status']='UNRESOLVED CONFLICT: no candidate within inferred median under current search limits'
 if d:
  x,y=group['center_xy'];dx,dy=d['delta_xy'];length=math.hypot(dx,dy);box('SHIFT_'+group['cap'],(x+dx/2,y+dy/2,.35),(length,.35,.35),orange,math.atan2(dy,dx),markers)
# Main remains original pier option; alternative excluded from main view layer only.
for c in [alt,markers]:main.view_layers[0].layer_collection.children[c.name].exclude=True
scene=bpy.data.scenes.new('STAGE05_ALTERNATIVE_PIERS_REVIEW')
for name in ['04_Elevated_deck_estimated','05_Parapets_estimated','06_Steel_girders_estimated','GROUND_FULL_01_OFFICIAL_AND_ESTIMATED','GROUND_FULL_02_CROSSINGS_AND_RAMPS_ESTIMATED',alt.name,markers.name]:scene.collection.children.link(bpy.data.collections[name])
camd=bpy.data.cameras.new('S45_ALT_CAMERA');cam=bpy.data.objects.new(camd.name,camd);scene.collection.objects.link(cam);scene.camera=cam;scene.world=main.world
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_cavity=True;scene.render.resolution_x=1700;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
changed=[r for r in p['groups'] if r['selected_for_comparison']] or [r for r in p['groups'] if r['original_overlap_m2']>.01];focus=min(changed,key=lambda r:math.dist(r['center_xy'],[1208,726]))
x,y=focus['center_xy'];cam.location=(x,y-85,65);cam.rotation_euler=(Vector((x,y,3))-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=95
scene.render.filepath=str(root/'pier_alternative.png');bpy.ops.render.render(write_still=True,scene=scene.name)
# Same camera for original supports: exchange collection links only within comparison scene.
scene.collection.children.unlink(alt);scene.collection.children.unlink(markers);scene.collection.children.link(bpy.data.collections['07_Piers_legacy_UNVERIFIED'])
scene.render.filepath=str(root/'pier_original.png');bpy.ops.render.render(write_still=True,scene=scene.name)
scene.collection.children.unlink(bpy.data.collections['07_Piers_legacy_UNVERIFIED']);scene.collection.children.link(alt);scene.collection.children.link(markers)
# Separate open-section display for selected underground cell, linked real elevated geometry.
section=bpy.data.scenes.new('STAGE04_B_SELECTED_OPEN_SECTION');section.world=main.world
for name in [ug.name,'04_Elevated_deck_estimated','07_Piers_legacy_UNVERIFIED']:section.collection.children.link(bpy.data.collections[name])
section.collection.objects.link(cam);section.camera=cam
# Independent camera copy to retain the alternative review view.
ucam=cam.copy();ucam.data=cam.data.copy();section.collection.objects.unlink(cam);section.collection.objects.link(ucam);section.camera=ucam
ucam.location=(1208,590,75);ucam.rotation_euler=(Vector((1208,726,-2))-ucam.location).to_track_quat('-Z','Y').to_euler();ucam.data.ortho_scale=225
section.render.engine='BLENDER_WORKBENCH';section.display.shading.color_type='MATERIAL';section.display.shading.show_cavity=True;section.render.resolution_x=1900;section.render.resolution_y=900;section.render.resolution_percentage=100;section.render.image_settings.file_format='PNG';section.render.filepath=str(root/'selected_depth_open_section.png');bpy.ops.render.render(write_still=True,scene=section.name)
bpy.context.window.scene=main
file=root/('STAGE45_SELECTED_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
result={'file':str(file),'chosen_levels':[-3.6,-7.2],'ramps':ramps,'pier_summary':p['summary'],'comparison_focus_cap':focus['cap'],'status':'Selected-depth test cell and estimated bent alternatives created. No actual underground perimeter, stair locations or foundation verified; no structural acceptance; B/C not passed.'};(root/'selected_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
