"""Save a reproducible work-model checkpoint without claiming field calibration is complete."""
import bpy,json,os,pathlib,math,collections,datetime,hashlib,shutil,tempfile
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1.;sc.unit_settings.length_unit='METERS';sc.view_layers[0].update()
files=['huashan_photo_shell_report.json','station_vent_photo_report.json','small_station_vent_photo_report.json','southwest_plant_photo_report.json','tiled_shaft_photo_report.json','additional_small_vent_photo_report.json','miramar_photo_shell_report.json','zhonglun_station_photo_report.json'];records=[];errors=[];meshes=0
for filename in files:
 r=json.load(open(out/filename))
 for row in r.get('items',[r]):
  coords=[]
  for name in row['objects']:
   o=sc.objects.get(name)
   if o is None or not o.visible_get():errors.append({'object':name,'error':'missing_or_hidden'});continue
   vs=[o.matrix_world@v.co for v in o.data.vertices];coords.extend(vs);meshes+=1
   if any(not math.isfinite(x) for v in vs for x in v):errors.append({'object':name,'error':'nonfinite'})
   ec=collections.Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in o.data.polygons for i in range(len(p.vertices)))
   if any(v!=2 for v in ec.values()):errors.append({'object':name,'error':'open_or_nonmanifold_edges'})
  records.append({'osm_id':row['osm_id'],'parts':len(row['objects']),'bottom_z_m':min(v.z for v in coords) if coords else None,'top_z_m':max(v.z for v in coords) if coords else None,'source_report':filename})
assert not errors,errors[:5]
source=json.load(open(out/'corrected_rows_context.json'));done={r['osm_id'] for r in records};remaining=[r for r in source if r['tags'].get('man_made')=='ventilation_shaft' and r['osm_id'] not in done];col=bpy.data.collections.get('VENTS_PENDING_PHOTO_CALIBRATION_0912')
if col is None:col=bpy.data.collections.new('VENTS_PENDING_PHOTO_CALIBRATION_0912');sc.collection.children.link(col)
for row in remaining:
 name='REVIEW_VENT_'+row['osm_id'];o=col.objects.get(name)
 if o is None:o=bpy.data.objects.new(name,None);col.objects.link(o)
 pts=row['geometry']['coordinates'][0][0];o.location=(sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts),row['base_z_m']+row['height_m']);o.empty_display_type='CIRCLE';o.empty_display_size=1.;o.show_in_front=True;o.hide_render=True;o['status']='Generic working model retained; exact shape/height still pending image or drawing calibration';o['osm_id']=row['osm_id']
markers=sorted([m for m in sc.timeline_markers if m.name.startswith('EW_1SEC_')],key=lambda m:m.frame);assert len(markers)==106 and len({m.camera.name for m in markers})==106;assert sc.render.fps==24 and sc.render.fps_base==1 and sc.frame_start==1 and sc.frame_end==2544;assert all(b.frame-a.frame==24 for a,b in zip(markers,markers[1:]));sc.frame_set(1)
r={'photo_informed_or_neighbor_inferred_vent_records':sum(x['osm_id'] in {r['osm_id'] for r in source if r['tags'].get('man_made')=='ventilation_shaft'} for x in records),'photo_or_inferred_assets_total':len(records),'component_meshes_checked':meshes,'geometry_errors':errors,'items':records,'remaining_generic_vents':[x['osm_id'] for x in remaining],'source_building_records':len(source),'first_row_source_records':sum(bool(x.get('first_row')) for x in source),'route_cameras':106,'fps':24,'frames':[1,2544],'main_scene':sc.name,'limitations':'Closed finite meshes and source coverage are not survey accuracy, whole-site completeness, physical clearance or regulatory certification. Individual photo reports distinguish observed features from assumed dimensions and inferred neighbors.'};(out/'photo_working_checkpoint_0912.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));sc['photo_working_checkpoint_0912']=json.dumps(r,ensure_ascii=False)
for stage in ['01','02','03']:
 sha=os.environ.get('CIVIC_BACKUP_STAGE'+stage)
 if sha:
  assert len(sha)==40 and all(c in '0123456789abcdef' for c in sha);sc['backup_stage'+stage]=sha
path=out/'CIVIC_FULL_CORRIDOR_WORKING_20260912.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
with tempfile.TemporaryDirectory(prefix='civic_scene_probe_') as tmp:
 probe=pathlib.Path(tmp)/'probe.blend';shutil.copy2(path,probe)
 with bpy.data.libraries.load(str(probe),link=True) as (available,unused):saved_scenes=set(available.scenes)
 required={sc.name,'GONGZHONG_INTEGRATED_OPENINGS_0912_EST','HUASHAN_PHOTO_REVIEW_0912','STATION_VENT_PHOTO_REVIEW_0912','SMALL_STATION_VENT_REVIEW_0912','SOUTHWEST_PLANT_REVIEW_0912','TILED_SHAFT_REVIEW_0912','ADDITIONAL_SMALL_VENT_REVIEW_0912','MIRAMAR_PHOTO_REVIEW_0912_V2','ZHONGLUN_STATION_REVIEW_0912'}
 assert required<=saved_scenes,sorted(required-saved_scenes)
(out/'checkpoint_manifest_0912.json').write_text(json.dumps({'file':str(path),'saved_at':datetime.datetime.now().isoformat(),'size_bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'verified_saved_scenes':sorted(required),'backup_commits':{stage:sc.get('backup_stage'+stage) for stage in ['01','02','03']},'main_scene':sc.name,'scope':r['limitations']},ensure_ascii=False,indent=2));result={'photo_or_inferred_assets':len(records),'meshes_checked':meshes,'errors':len(errors),'remaining_generic_vents':len(remaining),'file':path.name}
