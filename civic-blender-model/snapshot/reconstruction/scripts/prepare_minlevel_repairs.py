import os
import pathlib,json,math
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';rows=json.load(open(out/'tnh_rows_context.json'));tnh=set(json.load(open(out/'tnh_target_ids.json')));ids=[];audit=[]
for r in rows:
 t=r['tags'];oid=r['osm_id']
 if oid in tnh:continue
 if t.get('building:min_level'):
  lo=float(t['building:min_level']);levels=float(t.get('building:levels',0));height=r['height_m'];rh=float(t.get('roof:height',0));base=float(t['min_height']) if t.get('min_height') else lo*((height-rh)/levels if levels>0 else 3.3)
  if base>=height-.5:audit.append({'id':oid,'status':'CONFLICT min_level reaches top; retained original estimate pending tag/source review','base_candidate':base,'height':height});continue
  r['base_z_m']=base;r['height_status']+='; lower extent honors mapped min_level; floor spacing inferred';ids.append(oid);audit.append({'id':oid,'base_before':0,'base_after':base,'status':'OSM vertical range interpreted; absolute elevation estimated'})
 if t.get('amenity')=='shelter' and t.get('building')=='yes':
  r['tags']=dict(t);r['tags']['building']='roof';r['height_m']=3.3;r['height_status']='Shelter semantic correction;3.3m roof height estimated, not neighboring tower height';ids.append(oid);audit.append({'id':oid,'status':'Shelter class instead of tower; height estimated'})
(out/'corrected_rows_context.json').write_text(json.dumps(rows,ensure_ascii=False));(out/'minlevel_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2));(out/'minlevel_target_ids.json').write_text(json.dumps(ids))
s=pathlib.Path('reconstruction/scripts/prepare_facade_modules.py').read_text().replace("out=root/'BlockFacades';rows=json.load(open(out/'buildings_selected.json'))", "out=root/'CalibrationRound3';rows=json.load(open(out/'corrected_rows_context.json'))")
s=s.replace("out/'source/streets_plan_boundaries.json'","root/'BlockFacades/source/streets_plan_boundaries.json'")
s=s.replace('for r in rows:\n g=',"for r in rows:\n if r['osm_id'] not in "+repr(ids)+":continue\n g=")
s=s.replace("if canopy and 'height' not in t:","if canopy and 'height' not in t and t.get('amenity')!='shelter':")
s=s.replace("out/'facade_payload.json'","out/'minlevel_payload.json'").replace("out/'facade_summary.json'","out/'minlevel_summary.json'")
exec(compile(s,'<minlevel-facades>','exec'));print('targets',len(ids),'unresolved',len(audit)-len(ids))
