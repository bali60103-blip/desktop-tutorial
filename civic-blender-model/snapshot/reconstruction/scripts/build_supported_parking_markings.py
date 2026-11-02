import bpy,json,os,pathlib,datetime
from mathutils import Vector,Matrix
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();r=json.load(open(out/'supported_parking_markings_payload.json'));targets={x['object']:sc.objects[x['object']] for x in r['items']}
for row in r['items']:
 o=targets[row['object']];assert len(o.data.vertices)==len(row['source_vertices']);assert max((o.matrix_world@v.co-Vector(p)).length for v,p in zip(o.data.vertices,row['source_vertices']))<.001
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_MARKING_SUPPORT_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True)
cols=[]
for col in list(sc.collection.children):
 if not any(o.name in col.objects for o in targets.values()):continue
 state=sc.view_layers[0].layer_collection.children[col.name].exclude;clone=col.copy();clone.name='MARKING12_'+col.name;sc.collection.children.unlink(col);sc.collection.children.link(clone);sc.view_layers[0].layer_collection.children[clone.name].exclude=state;cols.append(clone)
report=[]
for row in r['items']:
 old=targets[row['object']];name=old.name;old.name='PRE_MARKING12_'+name;new=None
 if row['vertices']:
  origin=Vector(row['vertices'][0]);m=bpy.data.meshes.new(name);m.from_pydata([Vector(v)-origin for v in row['vertices']],[],row['faces']);m.update()
  for mat in old.data.materials:m.materials.append(mat)
  new=old.copy();new.name=name;new.data=m;new.matrix_world=Matrix.Translation(origin);new['support_clipped_0912']=True;new['status']='Estimated striping clipped to modeled slab, not surveyed stall layout'
 for col in cols:
  if old.name in col.objects:col.objects.unlink(old);new and col.objects.link(new)
 report.append({'object':name,'retained':old.name,'removed_area_m2':row['removed_area_m2'],'remaining_vertices':len(row['vertices'])})
(out/'supported_parking_markings_report.json').write_text(json.dumps({'checked':r['checked'],'corrected':len(report),'items':report,'scope':'Main-scene generated paint only. No floor or ramp geometry changed. Earlier scenes retain originals.'},ensure_ascii=False,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_UNDERGROUND_COMPLETION_20260912.blend'));result={'checked':r['checked'],'corrected':len(report)}
