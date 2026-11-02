"""Export per-station model heights and unresolved support pairs; no field measurements."""
import bpy,json,os,csv
ROOT=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
a=json.load(open(os.path.join(ROOT,'span_height_audit.json')))
rows=[]
for sp in a['spans']:
 for s in sp['samples']:
  vals=s['cross_samples']
  def extrema(key):
   v=[r[key] for r in vals if r.get(key) is not None]
   return (min(v),max(v)) if v else (None,None)
  ground=extrema('ground_z');soffit=extrema('soffit_z');top=extrema('deck_top_z')
  rows.append([sp['span_id'],'|'.join(sp['start_piers']),'|'.join(sp['end_piers']),s['fraction'],s['fraction']*sp['plan_length_m'],*s['xy'],*ground,*soffit,*top,s['sampled_min_clearance_m'],sum(v.get('ground_z') is not None for v in vals),len(vals),False])
with open(os.path.join(ROOT,'span_station_heights.csv'),'w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['span_id','start_piers','end_piers','fraction','distance_from_candidate_start_m','model_x','model_y','ground_z_min','ground_z_max','soffit_z_min','soffit_z_max','deck_top_z_min','deck_top_z_max','sampled_min_clearance_m','ground_hits','deck_hits','real_world_verified']);w.writerows(rows)
compact={k:v for k,v in a.items() if k!='spans'}
compact['spans']=[{k:v for k,v in s.items() if k!='samples'} for s in a['spans']]
json.dump(compact,open(os.path.join(ROOT,'span_height_summary.json'),'w'),ensure_ascii=False,indent=2)
checks={'span_count':len(a['spans']),'station_rows':len(rows),'expected_station_rows':11*len(a['spans']),'unique_span_ids':len({s['span_id'] for s in a['spans']}),'missing_clearance_spans':sum(s['sampled_min_clearance_m'] is None for s in a['spans']),'nonpositive_clearances':sum(r[13] is not None and r[13]<=0 for r in rows),'real_world_verified':False}
assert checks['station_rows']==checks['expected_station_rows']
assert checks['unique_span_ids']==checks['span_count']
json.dump(checks,open(os.path.join(ROOT,'span_export_checks.json'),'w'),indent=2)
result=checks
