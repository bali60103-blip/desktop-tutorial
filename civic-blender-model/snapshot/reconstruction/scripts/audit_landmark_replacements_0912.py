import bpy,json,os,pathlib,math,collections,shutil
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';s=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=s;s.view_layers[0].update();items=[];errors=[]
for fn in ['miramar_photo_shell_report.json','zhonglun_station_photo_report.json']:
 report=json.load(open(out/fn))
 for row in report.get('items',[report]):
  z=[]
  for name in row['objects']:
   o=s.objects.get(name)
   if not o or not o.visible_get():errors.append([name,'missing_or_hidden']);continue
   counts=collections.Counter(tuple(sorted(e)) for p in o.data.polygons for e in p.edge_keys)
   if any(v!=2 for v in counts.values()):errors.append([name,'non_closed_component'])
   for v in o.data.vertices:
    q=o.matrix_world@v.co
    if not all(math.isfinite(a) for a in q):errors.append([name,'non_finite'])
    z.append(q.z)
  items.append({'osm_id':row['osm_id'],'parts':len(row['objects']),'z_range':[min(z),max(z)],'height_estimate_m':row['height_estimate_m'],'source_url':row['source_url'],'status':'Photo-informed working estimate, not surveyed'})
markers=sorted([m for m in s.timeline_markers if m.camera],key=lambda m:m.frame)
assert len(markers)==106 and len({m.camera.name for m in markers})==106 and all(b.frame-a.frame==24 for a,b in zip(markers,markers[1:]))
r={'items':items,'errors':errors,'road_cameras':106,'fps':s.render.fps,'frames':[s.frame_start,s.frame_end],'all_dimensions_still_estimates':True};(out/'landmark_replacement_audit_0912.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));assert not errors
src=pathlib.Path(os.environ['CIVIC_SCRIPT_DIR'])
for n in ['build_miramar_photo_shell.py','refine_miramar_photo_shell.py','build_zhonglun_station_photo.py','audit_landmark_replacements_0912.py','reconcile_current_building_coverage.py']:shutil.copy2(src/n,out/'scripts'/n)
s['backup_stage01_commit']='993dd5a66b9e258ce06f77d731ca3cbe52d23637'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'CIVIC_FULL_CORRIDOR_WORKING_20260912.blend'));result=r
