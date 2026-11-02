import json,pathlib,math,ast,collections
from shapely.geometry import shape,Point
from shapely.geometry.polygon import orient
from shapely import set_precision,constrained_delaunay_triangles
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');selected=json.load(open(out/'buildings_selected.json'));payload=json.load(open(out/'facade_payload.json'));raw=next(r for r in json.load(open(out/'source/buildings.json')) if r['osm_id']=='w1347250436');g=shape(raw['geometry']);blocks=json.load(open(out/'blocks.json'));bid=max(blocks,key=lambda r:g.intersection(shape(r['geometry'])).area)['id'];record={'osm_id':raw['osm_id'],'name':'','tags':raw['tags'],'geometry':raw['geometry'],'block_id':bid,'first_row':True,'height_m':3.3,'base_z_m':0,'height_status':'OSM1floor x estimated3.3m','area_m2':g.area,'facade_status':'Small mapped frontage structure; estimated entry/window','is_building_part':False}
source=ast.parse(pathlib.Path('/tmp/civic-stage00/reconstruction/scripts/prepare_facade_modules.py').read_text());fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='extrude');exec(compile(ast.Module(body=[fn],type_ignores=[]),'mesh_function','exec'))
cores=[];points=[];door=False
for p in ([g] if g.geom_type=='Polygon' else g.geoms):
 p=orient(set_precision(p,.001));q=set_precision(p.buffer(-.19),.001)
 if q.is_empty:q=p
 for c in ([q] if q.geom_type=='Polygon' else q.geoms):
  if c.geom_type=='Polygon' and c.area>.001:cores.append(extrude(orient(c),0,2.75))
 cc=list(p.exterior.coords)
 for a,b in zip(cc,cc[1:]):
  L=math.dist(a,b)
  if L<.01:continue
  angle=math.atan2(b[1]-a[1],b[0]-a[0]);x=(a[0]+b[0])/2;y=(a[1]+b[1])/2;module=4 if L<1.1 else (3 if not door else 0)
  if module==3:door=True
  points.append({'position':[x,y,1.375],'scale':[L,1,2.75],'rotation':[0,0,angle],'module':module});points.append({'position':[x,y,3.025],'scale':[L,1,.55],'rotation':[0,0,angle],'module':4})
new={k:record[k] for k in ['osm_id','name','block_id','first_row','height_m','base_z_m','height_status','facade_status','is_building_part']};new.update(cores=cores,roofs=[],points=points)
if not any(r['osm_id']==new['osm_id'] for r in payload):payload.append(new);selected.append(record)
alias={'source_osm_id':'w1347249268','represented_by':'w1347249264','reason':'Coincident mapped footprint deduplicated; do not build overlapping duplicate facade'};(out/'frontage_coverage_alias.json').write_text(json.dumps(alias,ensure_ascii=False,indent=2));(out/'small_frontage_addition.json').write_text(json.dumps(new,ensure_ascii=False));(out/'facade_payload.json').write_text(json.dumps(payload,ensure_ascii=False));(out/'buildings_selected.json').write_text(json.dumps(selected,ensure_ascii=False));s=json.load(open(out/'selection_summary.json'));s['mapped_buildings_and_parts']=len(selected);s['first_row_buildings']=sum(r['first_row'] for r in selected);s['interior_buildings_and_parts']=sum(not r['first_row'] for r in selected);s['coincident_frontage_aliases']=[alias];s['small_frontage_retained_m2']=g.area;(out/'selection_summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2));fs=json.load(open(out/'facade_summary.json'));fs['building_records']=len(payload);fs['core_mesh_components']=sum(len(r['cores']) for r in payload);fs['facade_instances']=sum(len(r['points']) for r in payload);fs['module_counts']=dict(collections.Counter(str(p['module']) for r in payload for p in r['points']));(out/'facade_summary.json').write_text(json.dumps(fs,ensure_ascii=False,indent=2));print({'records':len(payload),'small_frontage_m2':g.area,'points':len(points),'alias':alias})
