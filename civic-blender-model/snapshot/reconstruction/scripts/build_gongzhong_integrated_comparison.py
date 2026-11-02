import bpy,json,pathlib,os,datetime
from mathutils import Vector,Matrix
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';source=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];name='GONGZHONG_INTEGRATED_OPENINGS_EST';assert not bpy.data.scenes.get(name),'Already built';payload=json.load(open(out/'gongzhong_integrated_openings_payload.json'));bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_GZ_INTEGRATED_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
scene=source.copy();scene.name=name;mapping={};states={lc.collection.name:lc.exclude for lc in source.view_layers[0].layer_collection.children}
for col in list(scene.collection.children):
 assert len(col.children)==0,'Nested collections need recursive isolation'
 clone=col.copy();clone.name='GZI_'+col.name;scene.collection.children.unlink(col);scene.collection.children.link(clone);mapping[col.name]=clone
for cname,clone in mapping.items():scene.view_layers[0].layer_collection.children[clone.name].exclude=states[cname]
replace={r['source']:r for r in payload['items']};shift=Vector(payload['translation']);objects=[]
for o in list(source.objects):
 moving=o.name.startswith(('COMP_公中_CORE0_L','RAIL_CORE_公中_0_','GUARD_CORE_公中_0_'));row=replace.get(o.name)
 if not moving and row is None:continue
 clone=o.copy();clone.name='GZI_'+o.name
 for oldname,col in mapping.items():
  if o.name in col.objects:col.objects.unlink(o);col.objects.link(clone)
 if row:
  vs=row['vertices'];origin=Vector(vs[0]);m=bpy.data.meshes.new(clone.name);m.from_pydata([tuple(Vector(v)-origin) for v in vs],[],row['faces']);m.update()
  for mat in o.data.materials:m.materials.append(mat)
  clone.data=m;clone.matrix_world=Matrix.Translation(origin);clone['old_core_hole_filled']=row['old_core_hole_filled']
 else:clone.location+=shift
 clone['integration_status']='Unadopted 5m estimate. Opening/road occupation requires real-world verification.';clone['source_object']=o.name;objects.append({'source':o.name,'copy':clone.name,'moved':moving,'opening_rebuilt':row is not None})
paths=json.load(open(out.parent/'Calibration/checked_paths.json'))
for p in paths:
 if p['id'].startswith('CORE_公中_0_'):
  p['a']=list(Vector(p['a'])+shift);p['b']=list(Vector(p['b'])+shift)
(out/'gongzhong_integrated_paths.json').write_text(json.dumps(paths,ensure_ascii=False,indent=2));scene['status']='INTEGRATED COMPARISON ONLY. Original working scene unchanged. Floors/roof/ground openings rebuilt, entrance location unverified.';scene['roof_collection']=mapping['COMPLETION_REMOVABLE_ROOFS'].name
report={'scene':name,'original_scene':source.name,'adopted':False,'moved_objects':sum(r['moved'] for r in objects),'opening_meshes_rebuilt':len(replace),'objects':objects,'translation':list(shift),'limits':['Estimated relocation, not surveyed entrance','New opening intersects modeled road surface; actual roadway/median classification unresolved','Other two conflicting cores not moved 105/140m; parking outline overlap retained','Full clearance check required after opening reconstruction']};(out/'gongzhong_integrated_model.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));bpy.context.window.scene=source;source.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={k:v for k,v in report.items() if k!='objects'}
