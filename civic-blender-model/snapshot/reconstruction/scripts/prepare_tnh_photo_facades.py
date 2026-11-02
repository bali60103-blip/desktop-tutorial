import os
import pathlib,json
from shapely.geometry import shape
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';out.mkdir(exist_ok=True)
rows=json.load(open(root/'BlockFacades/buildings_selected.json'));main=next(r for r in rows if r['osm_id']=='w229059792');g=shape(main['geometry']);ids=[r['osm_id'] for r in rows if r['osm_id']==main['osm_id'] or r['is_building_part'] and shape(r['geometry']).intersection(g).area>50]
ids=sorted(set(ids+['w644804950','w644804957','w644804958']))
for r in rows:
 if r['osm_id'] not in ids:continue
 r['tags']=dict(r['tags']);r['tags']['building:part']='commercial'
 if 'building:min_level' in r['tags']:r['base_z_m']=float(r['tags']['building:min_level'])*3.3
(out/'tnh_rows_context.json').write_text(json.dumps(rows,ensure_ascii=False));(out/'tnh_target_ids.json').write_text(json.dumps(ids))
s=pathlib.Path('reconstruction/scripts/prepare_facade_modules.py').read_text()
s=s.replace("out=root/'BlockFacades';rows=json.load(open(out/'buildings_selected.json'))", "out=root/'CalibrationRound3';rows=json.load(open(out/'tnh_rows_context.json'))")
s=s.replace("out/'source/streets_plan_boundaries.json'", "root/'BlockFacades/source/streets_plan_boundaries.json'")
s=s.replace('for r in rows:\n g=',"for r in rows:\n if r['osm_id'] not in "+repr(ids)+":continue\n g=")
s=s.replace('4.5 if kind==2 else 3.2','4.5')
s=s.replace('if cover:module=4','if False:module=4') # Keep grid on partially exposed bays; interior instances remain occluded by neighboring cores.
s=s.replace('p.buffer(-.19,join_style=2)','p.buffer(-.65,join_style=2)')
s=s.replace('Estimated repeating recessed-window modules and inferred entry; no street-photo correspondence claimed','Official exterior-photo-informed grid shading and recessed glazing; bay spacing, depth and absolute floor heights estimated; not full elevation survey')
exec(compile(s,'<tnh-facade-preparation>','exec'))
