"""Blender: reversible duplicate-cap cleanup, live support checks and isolated section options.
No surveyed underground footprint/levels or pier relocation is asserted. ROOT supplied.
"""
import bpy,json,pathlib,datetime,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=pathlib.Path(ROOT);root.mkdir(parents=True,exist_ok=True)
s=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');main=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(root/('before_stage45_'+s+'.blend')),copy=True)
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [min(v[i] for v in p) for i in range(3)]+[max(v[i] for v in p) for i in range(3)]
caps=[o for o in bpy.data.collections['07_Piers_legacy_UNVERIFIED'].objects if '_CAP_' in o.name];kept=[];duplicates=[]
for o in sorted(caps,key=lambda o:o.name):
 b=bounds(o);match=next((p for p,pb in kept if max(abs(x-y) for x,y in zip(b,pb))<.002),None)
 if match:
  # Verify world-space vertices too; matching boxes alone do not establish duplicates.
  a=[o.matrix_world@v.co for v in o.data.vertices];c=[match.matrix_world@v.co for v in match.data.vertices]
  if len(a)==len(c) and max(min((v-w).length for w in c) for v in a)<.002:
   duplicates.append({'hidden':o.name,'kept':match.name,'prior_hide_render':o.hide_render,'prior_hide_viewport':o.hide_get()});o.hide_render=True;o.hide_set(True);o['stage45_duplicate_of']=match.name;continue
 kept.append((o,b))
# Upward rays against actual girder meshes, not convex deck envelopes.
vs=[];fs=[]
for o in bpy.data.collections['06_Steel_girders_estimated'].objects:
 off=len(vs);vs.extend([o.matrix_world@v.co for v in o.data.vertices]);fs.extend([[i+off for i in f.vertices] for f in o.data.polygons])
bvh=BVHTree.FromPolygons(vs,fs,all_triangles=False);checks=[]
for o,b in kept:
 hits=[]
 for v in o.data.vertices:
  w=o.matrix_world@v.co
  if abs(w.z-b[5])>.002:continue
  hit,normal,idx,dist=bvh.ray_cast(w+Vector((0,0,.001)),Vector((0,0,1)),5)
  if hit is not None:hits.append(hit.z-b[5])
 checks.append({'cap':o.name,'center_xy':[(b[0]+b[3])/2,(b[1]+b[4])/2],'corner_ray_hits':len(hits),'minimum_positive_gap_m':min(hits) if hits else None,'status':'Corner rays only; no hit does not prove missing support. Local solid contact and bearing design unresolved.'})
# Main-scene pilot outline and source-only entry markers. No underground hull forced into georeferenced scene.
name='WORKSHEET04_ZHONGLIN_REVIEW_ONLY';col=bpy.data.collections.get(name)
if not col:col=bpy.data.collections.new(name);main.collection.children.link(col)
for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
for nm,loc in [('PILOT_CENTER',(1208.59,726.42,0)),('WEST_OSM_CANDIDATE',(1128.846965,731.106122,0)),('EAST_OSM_CANDIDATE',(1288.333559,721.741783,0))]:
 o=bpy.data.objects.new(nm,None);col.objects.link(o);o.location=loc;o.empty_display_type='CIRCLE';o.empty_display_size=4;o.show_name=True;o.show_in_front=True;o['status']='Review reference; underground elevation unknown'
# Separate comparison scene: explicit schematic axes, NOT georeferenced underground placement.
old=bpy.data.scenes.get('STAGE04_DEPTH_OPTIONS_SCHEMATIC')
if old:bpy.data.scenes.remove(old)
scene=bpy.data.scenes.new('STAGE04_DEPTH_OPTIONS_SCHEMATIC');scene['status']='Schematic dimension comparison only. Not registered parking layout.'
def mat(name,color):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
roadmat=mat('S45_Road',(.16,.19,.21));concrete=mat('S45_Concrete',(.62,.65,.67));blue=mat('S45_Level',(.16,.44,.68));ink=mat('S45_Text',(.05,.07,.09));orange=mat('S45_Assumed',(.85,.4,.12))
def box(name,x,y,z,dx,dy,dz,m):
 vs=[(x+sx*dx/2,y+sy*dy/2,z+sz*dz/2) for sx,sy,sz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]);me.materials.append(m);o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o['status']='SCHEMATIC ASSUMPTION, not site geometry';return o

def label(name,text,x,z,size=.65):
 cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.size=size;cu.extrude=0;cu.materials.append(ink);o=bpy.data.objects.new(name,cu);scene.collection.objects.link(o);o.location=(x,-1.1,z);o.rotation_euler=(math.pi/2,0,0)
options=[]
for tag,x,d in [('A',-24,3.0),('B',24,3.6)]:
 label(tag+'_title',f'{tag} | ASSUMED LEVELS',x-18,12,1)
 label(tag+'_legend','SCHEMATIC - NOT AS-BUILT',x-18,10.3,.65)
 box(tag+'_ground',x,0,-.125,36,1,.25,roadmat)
 box(tag+'_deck',x,0,7.825,23.5,1,.35,concrete)
 box(tag+'_girder',x,0,6.625,22,1,2.05,concrete)
 for xx in [-3,3]:box(tag+'_pier',x+xx,0,2.4,2,1,4.8,concrete)
 box(tag+'_cap',x,0,5.2,10,1,.8,concrete)
 for level in [1,2]:
  z=-d*level;box(tag+'_B'+str(level),x,0,z-.15,24,1,.3,blue)
  label(tag+'_level'+str(level),f'B{level}: {z:.1f} m',x+12.5,z,.65)
 label(tag+'_zero','GROUND: 0.0 m',x+12.5,.5,.6)
 label(tag+'_note',f'Floor spacing {d:.1f} m | slab assumed 0.30 m',x-18,-10,.6)
 label(tag+'_ramp',f'10% grade test: {d/0.1:.0f} m / level (no transitions)',x-18,-11.2,.6)
 label(tag+'_width','24 m hull width = display assumption only',x-18,-12.4,.6)
 options.append({'option':tag,'B1_m':-d,'B2_m':-2*d,'slab_assumed_m':.3,'slab_to_slab_clear_m':d-.3,'test_grade':.1,'straight_ramp_run_per_level_m':d/.1,'limitations':'No beams/services allowance; grade not a code recommendation. Footprint width 24m is schematic only; no entrance or stair placement asserted.'})
camd=bpy.data.cameras.new('S45_OPTION_CAMERA');cam=bpy.data.objects.new(camd.name,camd);scene.collection.objects.link(cam);cam.location=(0,-100,0);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=95;scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=False;scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('S45_White');scene.world.color=(.8,.8,.8);scene.render.resolution_x=2200;scene.render.resolution_y=850;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(root/'depth_options.png')
bpy.ops.render.render(write_still=True,scene=scene.name)
# Restore main scene and render its actual integrated ground/elevated pilot.
bpy.context.window.scene=main;cam=main.camera;old=(cam.location.copy(),cam.rotation_euler.copy(),cam.data.ortho_scale)
cam.location=(1210,530,145);cam.rotation_euler=(Vector((1210,728,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=245
main.render.resolution_x=1800;main.render.resolution_y=1000;main.render.filepath=str(root/'stage45_integrated_pilot.png');bpy.ops.render.render(write_still=True)
cam.location,cam.rotation_euler,cam.data.ortho_scale=old
file=root/('STAGE45_REVIEW_'+s+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file))
result={'file':str(file),'duplicate_caps_hidden':len(duplicates),'active_caps':len(kept),'duplicates':duplicates,'local_support_checks':checks,'depth_options':options,'status':'04 sample review and 05 duplicate-cap repair; underground alternative selection pending; no pier XY moved; gates B/C not passed'}
(root/'stage45_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));result={'file':str(file),'duplicate_caps_hidden':len(duplicates),'active_caps':len(kept),'comparison':str(root/'depth_options.png'),'pilot_render':str(root/'stage45_integrated_pilot.png')}
