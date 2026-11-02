import bpy,pathlib,json,datetime,collections
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';p=json.load(open(out/'access_payload.json'));sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];bpy.context.window.scene=sc;stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_access_'+stamp+'.blend')),copy=True)
col=bpy.data.collections.new('COMPLETION_SURFACE_ACCESS');sc.collection.children.link(col);mat=bpy.data.materials['COMPLETION_ASSUMED_PARKING'];archived=[]
for part in p['parts']:
 m=part['mesh'];vs=m['vertices'];fs=[list(f) for f in m['faces']];ec=collections.Counter(tuple(sorted((a,b))) for f in fs for a,b in zip(f,f[1:]+f[:1]));assert all(n==2 for n in ec.values()),part['name'];me=bpy.data.meshes.new(part['name']);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(part['name'],me);me.materials.append(mat);target=bpy.data.collections['COMPLETION_REMOVABLE_ROOFS'] if part.get('replaces') else col;target.objects.link(o);o['verification_status']=part['status']
 if part.get('replaces'):
  old=bpy.data.objects[part['replaces']]
  if old.name not in archived:
   # Unlink from assembled roof collection; object data retained in a hidden archive collection.
   ac=bpy.data.collections.get('COMPLETION_ARCHIVED_ROOFS') or bpy.data.collections.new('COMPLETION_ARCHIVED_ROOFS');ac.objects.link(old);target.objects.unlink(old);archived.append(old.name)
for r in p['ramps']:
 name=r['name']+'_CAMERA';cd=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,cd);sc.collection.objects.link(cam);a=Vector(r['start']);b=Vector(r['end']);d=(b-a).normalized();cam.location=a-d*2+Vector((0,0,1.6));cam.rotation_euler=(b+Vector((0,0,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();cd.lens=24;cd.clip_end=30000;cam['status']='Assumed ramp camera; uncalibrated entry'
 marker=bpy.data.objects.new('QA_'+r['name'],None);bpy.data.collections['COMPLETION_ISSUE_MARKERS'].objects.link(marker);marker.location=r['start'];marker.empty_display_type='CIRCLE';marker.empty_display_size=3;marker['issue']='Entry identity, direction, grade and ground/median opening need imagery review'
# Add the authoritative existing road camera collection, without cloning its cameras.
cc=bpy.data.collections.get('CIVIC_CAMERAS_200M_NORTH_SOUTH')
if cc and cc.name not in sc.collection.children:sc.collection.children.link(cc)
sc.view_layers[0].update();cam=bpy.data.objects['FRONTAGE_HEIGHT_CAMERA'];sc.camera=cam;old=cam.matrix_world.copy();scale=cam.data.ortho_scale;clip=cam.data.clip_end;cam.data.clip_end=50000;lc=sc.view_layers[0].layer_collection;states={c.name:c.exclude for c in lc.children}
try:
 for label,center,offset,width,cut in [('全段',Vector((4800,850,0)),Vector((0,-7000,7000)),11500,False),('中林地下',Vector((1200,730,-3.6)),Vector((60,-90,95)),165,True)]:
  for name in ['COMPLETION_GROUND_HIGHWAY','COMPLETION_FRONTAGE','COMPLETION_MALLS','COMPLETION_EQUIPMENT']:lc.children[name].exclude=cut
  cam.location=center+offset;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=width;sc.view_layers[0].update();sc.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
finally:
 for name,val in states.items():lc.children[name].exclude=val
 cam.matrix_world=old;cam.data.ortho_scale=scale;cam.data.clip_end=clip;sc.view_layers[0].update()
file=out/('CIVIC_COMPLETION_ACCESS_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'new_surface_ramps':len(p['ramps']),'new_meshes':len(p['parts']),'new_ramp_cameras':len(p['ramps']),'roof_openings_updated':archived,'nonmanifold_edges_new':0,'issues':p['issues'],'limits':'Ground/median excavation and inlet-to-road transitions remain flagged, no claim of continuous road-to-parking clearance'};(out/'access_check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={k:v for k,v in r.items() if k!='issues'}
