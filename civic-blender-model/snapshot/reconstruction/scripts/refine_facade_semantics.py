import json,pathlib,collections
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');rows=json.load(open(out/'facade_payload.json'));source={r['osm_id']:r for r in json.load(open(out/'buildings_selected.json'))};changes=[]
for r in rows:
 t=source[r['osm_id']]['tags'];name=r['name'];kind=t.get('building:part',t.get('building',''));special=None
 if kind in ['temple','church','cathedral','shrine','mosque'] or t.get('amenity')=='place_of_worship':special=4
 elif kind in ['school','university','college','kindergarten'] or t.get('amenity') in ['school','university','college','kindergarten']:special=1
 elif any(s in name for s in ['作業場','作業廠','蒸餾','工坊','酒廠','包裝作業','維修工場','四連棟']):special=2
 if special is None:continue
 count=0
 for p in r['points']:
  if p['module'] in [0,1,2,5] and p['module']!=special:p['module']=special;count+=1
 if count:changes.append({'osm_id':r['osm_id'],'name':name,'changed_instances':count,'module':special,'reason':'Avoid residential balcony/window templates on worship, institutional or historic industrial categories; actual facade still unverified'})
(out/'facade_payload.json').write_text(json.dumps(rows,ensure_ascii=False));(out/'semantic_refinements.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2));summary=json.load(open(out/'facade_summary.json'));summary['module_counts']=dict(collections.Counter(str(p['module']) for r in rows for p in r['points']));summary['semantic_refinement_buildings']=len(changes);(out/'facade_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print({'buildings_refined':len(changes),'modules_refined':sum(r['changed_instances'] for r in changes)})
