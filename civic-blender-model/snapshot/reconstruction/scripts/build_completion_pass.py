"""Build a separate all-layer working assembly; preserve originals and mark estimates."""
import bpy,json,pathlib,datetime,collections
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';p=json.load(open(out/'payload.json'));stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
assert not bpy.data.scenes.get('CIVIC_COMPLETE_WORKING_ASSEMBLY'),'Already built; inspect existing checkpoint before rerun'
bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_completion_'+stamp+'.blend')),copy=True)
sc=bpy.data.scenes.new('CIVIC_COMPLETE_WORKING_ASSEMBLY');sc.world=bpy.data.scenes['Scene'].world
cols={}
for k in ['GROUND_HIGHWAY','FRONTAGE','PARKING','MARKINGS','EQUIPMENT','MALLS','REMOVABLE_ROOFS','ISSUE_MARKERS']:
 col=bpy.data.collections.new('COMPLETION_'+k);sc.collection.children.link(col);cols[k]=col
linked=set()
def link(o,key):
 if o.name not in linked:cols[key].objects.link(o);linked.add(o.name)
def visible(lc):
 if lc.exclude or lc.collection.hide_render:return []
 return [o for o in lc.collection.objects if not o.hide_render]+[o for child in lc.children for o in visible(child)]
for o in visible(bpy.data.scenes['Scene'].view_layers[0].layer_collection):
 if o.type in ['MESH','CURVE','FONT','LIGHT'] and o.name!='Buildings_context__OSM_XY__HEIGHTS_UNVERIFIED':link(o,'GROUND_HIGHWAY')
for o in bpy.data.collections['FRONTAGE_FULL_HEIGHT_COMPARISON'].objects:link(o,'FRONTAGE')
for o in bpy.data.scenes['PARKING_SECTIONS_COMPARISON'].objects:
 if o.type=='MESH' and 'B1_B2_RAMP' in o.name:link(o,'PARKING')
for o in bpy.data.scenes['Y_MALL_ENTRANCE_COMPARISON'].objects:
 if o.type=='MESH' and not o.hide_viewport:
  link(o,'REMOVABLE_ROOFS' if 'ROOF' in o.name.upper() else 'MALLS')
for o in bpy.data.scenes['UNDERGROUND_SHELL_COMPARISON'].objects:
 if o.type=='MESH' and ('Zhongshan' in o.name or 'ZhongxiaoW' in o.name):link(o,'REMOVABLE_ROOFS' if 'ROOF' in o.name.upper() else 'MALLS')
colors={'FRONTAGE':(.65,.46,.24,1),'PARKING':(.45,.52,.55,1),'MARKINGS':(.92,.86,.51,1),'EQUIPMENT':(.85,.42,.13,1)};mats={}
for k,c in colors.items():
 m=bpy.data.materials.new('COMPLETION_ASSUMED_'+k);m.diffuse_color=c;mats[k]=m
qa=[]
for part in p['parts']:
 data=part['mesh'];vs=data['vertices'];fs=data['faces'];assert all(len(f)==len(set(f)) for f in fs),part['name'];ec=collections.Counter(tuple(sorted((a,b))) for f in fs for a,b in zip(f,f[1:]+f[:1]));bad=sum(n!=2 for n in ec.values());assert not bad,(part['name'],bad)
 me=bpy.data.meshes.new(part['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(part['name'],me);key=part['group'];cols['REMOVABLE_ROOFS' if part['extra'].get('cutaway_roof') else key].objects.link(o);me.materials.append(mats[key]);o['verification_status']=part['status'];o['source_metadata']=json.dumps(part['extra'],ensure_ascii=False);o['completion_pass']='20260910 working volumes';qa.append({'object':o.name,'nonmanifold_edges':bad})
for issue in p['issues']:
 xy=issue.get('xy')
 if xy is None and issue['id'].startswith('PIER_'):
  token='Pier_'+issue['id'].split('_')[1];matches=[o for o in bpy.data.objects if o.name.startswith('UNVERIFIED_'+token) and o.type=='MESH']
  if matches:
   pts=[o.matrix_world@Vector(v) for o in matches for v in o.bound_box];xy=[sum(v.x for v in pts)/len(pts),sum(v.y for v in pts)/len(pts)]
 if xy is None:continue
 o=bpy.data.objects.new('QA_'+issue['id'],None);cols['ISSUE_MARKERS'].objects.link(o);o.location=(*xy,2);o.empty_display_type='CIRCLE';o.empty_display_size=2;o.color=(1,.18,.04,1);o['issue']=json.dumps(issue,ensure_ascii=False)
# Keep existing road/parking cameras, without creating duplicates.
for o in bpy.data.objects:
 if o.type=='CAMERA' and (o.name.startswith('CIVIC_200M') or o.name.startswith('RAMP_CAM') or o.name.endswith('_B1_B2_CAMERA')):
  if o.name not in sc.objects:sc.collection.objects.link(o)
cam=bpy.data.objects.get('FRONTAGE_HEIGHT_CAMERA');sc.collection.objects.link(cam);sc.camera=cam
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=False;sc.display.shading.show_cavity=True;sc.render.resolution_x=1600;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
bpy.context.window.scene=sc
sc.view_layers[0].update()
cols['REMOVABLE_ROOFS']['instructions']='Toggle collection for above-ground / underground cutaway; roof heights assumed.';sc.view_layers[0].layer_collection.children[cols['REMOVABLE_ROOFS'].name].exclude=True
old=cam.matrix_world.copy();scale=cam.data.ortho_scale
try:
 for label,center,offset,width in [('全段',Vector((4800,850,0)),Vector((0,-8500,8000)),11500),('中林地下',Vector((1200,730,-3.6)),Vector((60,-90,95)),165)]:
  cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=width;sc.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
finally:cam.matrix_world=old;cam.data.ortho_scale=scale
bpy.context.window.scene=sc
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  sp=area.spaces.active;sp.clip_end=30000;sp.region_3d.view_location=(4800,850,0);sp.region_3d.view_distance=9000
file=out/('CIVIC_COMPLETION_WORKING_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'scene':sc.name,'new_meshes':len(qa),'group_counts':p['counts'],'new_mesh_nonmanifold_edges':0,'issue_markers':len(cols['ISSUE_MARKERS'].objects),'total_scene_objects':len(sc.objects),'limits':'Working source-covered geometry only; layout, elevations, landmark heights and entrances remain estimated. Some retained underground alternatives overlap. Satellite/streetview calibration deferred per user.'};(out/'build_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
