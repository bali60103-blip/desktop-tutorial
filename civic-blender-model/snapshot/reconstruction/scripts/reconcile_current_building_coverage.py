"""Reconcile selected source records against current photo/equipment replacements."""
import bpy,json,os,pathlib
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;report=json.load(open(out/'current_completion_audit_0912.json'));vent=json.load(open(out/'mapped_vent_shell_report.json'));replacements={x['osm_id']:x['new_object'] for x in vent['items']};replacements['w1342705709']='RAILWAY_CHIMNEY_45M_BODY'
for filename in ['huashan_photo_shell_report.json','station_vent_photo_report.json','small_station_vent_photo_report.json','southwest_plant_photo_report.json','tiled_shaft_photo_report.json','additional_small_vent_photo_report.json','miramar_photo_shell_report.json','zhonglun_station_photo_report.json']:
 path=out/filename
 if not path.exists():continue
 r=json.load(open(path));rows=r.get('items',[r])
 for row in rows:
  if row.get('osm_id') and row.get('objects'):replacements[row['osm_id']]=row['objects'][0]
resolved=[];unresolved=[]
for row in report['missing_exact_core_names']:
 name=replacements.get(row['osm_id']);o=sc.objects.get(name) if name else None
 if o and o.visible_get():resolved.append({'osm_id':row['osm_id'],'replacement':name,'first_row':row['first_row']})
 else:unresolved.append(row)
r={'source_records':report['source_building_records'],'original_cores_visible':report['visible_core_matches'],'visible_replacements':resolved,'unresolved_missing_geometry':unresolved,'scope':'Selected OSM record coverage including equipment and photo-informed replacements. Not address-level completeness or photo-calibrated facade certification.'};(out/'current_building_coverage_0912.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));result={'source_records':r['source_records'],'original_visible':r['original_cores_visible'],'replacement_visible':len(resolved),'missing':len(unresolved)}
