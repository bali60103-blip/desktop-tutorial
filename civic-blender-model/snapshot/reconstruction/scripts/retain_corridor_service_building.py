import json,pathlib,math,ast,collections
from shapely.geometry import shape
from shapely.geometry.polygon import orient
from shapely import set_precision,constrained_delaunay_triangles
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/BlockFacades');rows=json.load(open(out/'buildings_selected.json'));payload=json.load(open(out/'facade_payload.json'));raw=next(r for r in json.load(open(out/'source/buildings.json')) if r['osm_id']=='r16131193');g=shape(raw['geometry']);source=ast.parse(pathlib.Path('/tmp/civic-stage00/reconstruction/scripts/prepare_facade_modules.py').read_text());fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='extrude');exec(compile(ast.Module(body=[fn],type_ignores=[]),'mesh_function','exec'));cores=[];points=[];door=False
for p in ([g] if g.geom_type=='Polygon' else g.geoms):
 p=orient(set_precision(p,.001));core=set_precision(p.buffer(-.19,join_style=2),.001)
 for c in ([core] if core.geom_type=='Polygon' else core.geoms):
  if c.geom_type=='Polygon' and c.area>.001:cores.append(extrude(orient(c),0,6.05))
 for ring in [p.exterior,*p.interiors]:
  cc=list(ring.coords)
  for a,b in zip(cc,cc[1:]):
   L=math.dist(a,b)
   if L<.02:continue
   n=max(1,round(L/4.5));angle=math.atan2(b[1]-a[1],b[0]-a[0]);w=L/n
   for j in range(n):
    x=a[0]+(b[0]-a[0])*(j+.5)/n;y=a[1]+(b[1]-a[1])*(j+.5)/n
    for lev in range(2):
     kind=4 if w<1.1 else (3 if lev==0 and not door else 2)
     if kind==3:door=True
     points.append({'position':[x,y,(lev+.5)*3.025],'scale':[w,1,3.025],'rotation':[0,0,angle],'module':kind})
    points.append({'position':[x,y,6.325],'scale':[w,1,.55],'rotation':[0,0,angle],'module':4})
r={'osm_id':raw['osm_id'],'name':'OSM corridor service building','block_id':'CORRIDOR_SERVICE','first_row':True,'height_m':6.6,'base_z_m':0,'height_status':'OSM2floors x estimated3.3m','facade_status':'Mapped service-building footprint; entry and louvers estimated','is_building_part':False,'cores':cores,'roofs':[],'points':points}
if not any(x['osm_id']==r['osm_id'] for x in payload):
 payload.append(r);sel={k:v for k,v in r.items() if k not in ['cores','roofs','points']};sel.update(tags=raw['tags'],geometry=raw['geometry'],area_m2=g.area);rows.append(sel)
relations={'r6075184','r16066283','r16131193','r17934959'}
for x in rows+payload:
 if x['osm_id'] in relations:x['first_row']=True
(out/'corridor_service_addition.json').write_text(json.dumps(r,ensure_ascii=False));(out/'facade_payload.json').write_text(json.dumps(payload,ensure_ascii=False));(out/'buildings_selected.json').write_text(json.dumps(rows,ensure_ascii=False));s=json.load(open(out/'selection_summary.json'));s.update(mapped_buildings_and_parts=len(rows),first_row_buildings=sum(x['first_row'] for x in rows),interior_buildings_and_parts=sum(not x['first_row'] for x in rows),retained_corridor_service_relations=['r16131193']);(out/'selection_summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2));fs=json.load(open(out/'facade_summary.json'));fs.update(building_records=len(payload),core_mesh_components=sum(len(x['cores']) for x in payload),facade_instances=sum(len(x['points']) for x in payload),module_counts=dict(collections.Counter(str(p['module']) for x in payload for p in x['points'])));(out/'facade_summary.json').write_text(json.dumps(fs,ensure_ascii=False,indent=2));print({'records':len(payload),'relation_centroid':list(g.centroid.coords)[0],'relation_points':len(points),'first_row_unique':s['first_row_buildings']})
