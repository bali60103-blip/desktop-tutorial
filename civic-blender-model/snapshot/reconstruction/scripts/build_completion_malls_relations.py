import bpy,pathlib,json,datetime,collections
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];bpy.context.window.scene=sc;stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('before_mall_details_'+stamp+'.blend')),copy=True);qa=[];issues=[]
for payload,colname,matname in [('malls_payload.json','COMPLETION_MALLS','COMPLETION_ASSUMED_PARKING'),('relations_payload.json','COMPLETION_FRONTAGE','COMPLETION_ASSUMED_FRONTAGE')]:
 p=json.load(open(out/payload));issues.extend(p['issues'])
 for part in p['parts']:
  assert not bpy.data.objects.get(part['name']),part['name'];m=part['mesh'];fs=[list(f) for f in m['faces']];assert all(len(f)==len(set(f)) for f in fs);ec=collections.Counter(tuple(sorted((a,b))) for f in fs for a,b in zip(f,f[1:]+f[:1]));assert all(n==2 for n in ec.values()),part['name'];me=bpy.data.meshes.new(part['name']);me.from_pydata(m['vertices'],[],fs);me.update();o=bpy.data.objects.new(part['name'],me);bpy.data.collections[colname].objects.link(o);me.materials.append(bpy.data.materials[matname]);o['verification_status']=part['status'];o['source_tags']=json.dumps(part.get('tags',{}),ensure_ascii=False);qa.append(o.name)
for r in issues:
 o=bpy.data.objects.new('QA_'+r['id'],None);bpy.data.collections['COMPLETION_ISSUE_MARKERS'].objects.link(o);o.location=(*r['xy'],2);o.empty_display_type='CIRCLE';o.empty_display_size=2;o['issue']=json.dumps(r,ensure_ascii=False)
# Named presets within this scene: hide surface collections to inspect underground geometry.
sc['WORKFLOW']='First-pass estimated massing. Toggle COMPLETION_GROUND_HIGHWAY/FRONTAGE/REMOVABLE_ROOFS for underground cutaway; QA_* objects store deferred corrections.'
allissues=[]
for f in ['payload.json','access_payload.json','malls_payload.json','relations_payload.json']:allissues.extend(json.load(open(out/f))['issues'])
text=bpy.data.texts.get('CIVIC_DEFERRED_ISSUES.json') or bpy.data.texts.new('CIVIC_DEFERRED_ISSUES.json');text.clear();text.write(json.dumps(allissues,ensure_ascii=False,indent=2));(out/'all_deferred_issues.json').write_text(text.as_string())
sc.view_layers[0].update();lc=sc.view_layers[0].layer_collection;states={c.name:c.exclude for c in lc.children};cam=bpy.data.objects['FRONTAGE_HEIGHT_CAMERA'];old=cam.matrix_world.copy();scale=cam.data.ortho_scale;clip=cam.data.clip_end;sc.camera=cam;cam.data.clip_end=50000
try:
 # Keep surface off in mall close-up.
 for n in ['COMPLETION_GROUND_HIGHWAY','COMPLETION_FRONTAGE','COMPLETION_PARKING','COMPLETION_MARKINGS','COMPLETION_EQUIPMENT','COMPLETION_SURFACE_ACCESS']:lc.children[n].exclude=True
 center=Vector((480,890,-2));cam.location=center+Vector((60,-70,75));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=150;sc.view_layers[0].update();sc.render.filepath=str(out/'地下街工作量體.png');bpy.ops.render.render(write_still=True,scene=sc.name)
finally:
 for name,val in states.items():lc.children[name].exclude=val
 cam.matrix_world=old;cam.data.ortho_scale=scale;cam.data.clip_end=clip;sc.view_layers[0].update()
file=out/('CIVIC_FULL_WORKING_PASS_'+stamp+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(file));r={'file':str(file),'new_meshes':len(qa),'new_nonmanifold_edges':0,'all_deferred_issue_count':len(allissues),'total_assembly_objects':len(sc.objects),'collection_objects':{c.name:len(c.objects) for c in sc.collection.children},'limits':'First-pass source-covered assembly; unverified features remain provisional. Flags are not repaired by imagery yet. No as-built or all-path clearance claim.'};(out/'completion_checkpoint.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result=r
