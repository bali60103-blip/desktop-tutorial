import bpy,json,pathlib,os,datetime
from mathutils import Vector,Matrix
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();r=json.load(open(out/'bottom_notch_closure_payload.json'));inventory={x['object']:x for x in json.load(open(out/'bottom_floor_opening_inventory.json'))};targets={x['object']:bpy.data.objects[x['object']] for x in r['items']}
for name,o in targets.items():
 assert not o.get('bottom_notch_closed_0912'),name+' already repaired';old=inventory[name]['vertices'];assert len(old)==len(o.data.vertices);assert max((o.matrix_world@v.co-Vector(p)).length for v,p in zip(o.data.vertices,old))<.001,name
bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_BOTTOM_NOTCHES_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.blend')),copy=True);activecols=[]
# Clone affected root collections so earlier scenes retain the original floor geometry.
for col in list(sc.collection.children):
 if not any(o.name in col.objects for o in targets.values()):continue
 state=sc.view_layers[0].layer_collection.children[col.name].exclude;clone=col.copy();clone.name='BOTTOM_NOTCH12_'+col.name;sc.collection.children.unlink(col);sc.collection.children.link(clone);sc.view_layers[0].layer_collection.children[clone.name].exclude=state;activecols.append(clone)
report=[]
for row in r['items']:
 old=targets[row['object']];oldname=old.name;old.name='PRE_BOTTOM_NOTCH12_'+oldname;origin=Vector(row['vertices'][0]);m=bpy.data.meshes.new('BOTTOM_NOTCH12_'+oldname);m.from_pydata([tuple(Vector(v)-origin) for v in row['vertices']],[],row['faces']);m.update()
 for mat in old.data.materials:m.materials.append(mat)
 new=old.copy();new.name=oldname;new.data=m;new.matrix_world=Matrix.Translation(origin);new['bottom_notch_closed_0912']=True;new['verification_status']='Estimated bottom stair notch restored inside the original parking footprint; no stair movement or field survey.'
 for col in activecols:
  if old.name in col.objects:col.objects.unlink(old);col.objects.link(new)
 for scene in bpy.data.scenes:
  if scene.name!='GONGZHONG_INTEGRATED_OPENINGS_0912_EST':continue
  for col in scene.collection.children:
   if old.name in col.objects:col.objects.unlink(old);col.objects.link(new)
 report.append({'object':new.name,'retained_object':old.name,'area_added_m2':row['area_added_m2'],'closed_core_paths':row['closed_core_paths']})
r={'floors_repaired':len(report),'stair_voids_closed':sum(len(x['closed_core_paths']) for x in report),'area_added_m2':sum(x['area_added_m2'] for x in report),'items':report,'unmatched':r['unmatched'],'scope':r['scope']};(out/'bottom_notch_closure_report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_UNDERGROUND_COMPLETION_20260912.blend'));result={k:v for k,v in r.items() if k!='items'}
