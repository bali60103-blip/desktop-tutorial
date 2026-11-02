"""Full named Civic Blvd ground working model. Official surfaces plus tagged OSM fallback.
Working extents are clipped to 70m around named ground routes; never interpreted as street width.
"""
import argparse,json,pathlib,re,math,collections
import shapefile
from shapely.geometry import shape,LineString,Point,box
from shapely import constrained_delaunay_triangles
from shapely.ops import unary_union,transform,triangulate
from pyproj import Transformer
p=argparse.ArgumentParser()
for n in ['routes','sidewalks','roads','registration','out']:p.add_argument('--'+n,required=True)
a=p.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True);reg=json.load(open(a.registration));f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in (0,1)];tr=Transformer.from_crs(4326,3826,always_xy=True)
def local(x,y,z=None):
 x,y=x-org[0],y-org[1];return ((math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale'])
def ll(x,y,z=None):return local(*tr.transform(x,y))
routes=[]
for ft in json.load(open(a.routes))['features']:
 t=ft['properties']
 if re.fullmatch('市民大道[一二三四五六七八]段',t.get('name','')) and t.get('bridge')!='yes' and t.get('tunnel')!='yes':routes.append((t,transform(ll,shape(ft['geometry']))))
assert len(routes)>90
axis=unary_union([g for t,g in routes]);study=axis.buffer(70);query=axis.buffer(5);bounds=study.bounds
roads=[];roadids=[]
for sr in shapefile.Reader(a.roads).iterShapeRecords():
 b=sr.shape.bbox;bl=local(b[0],b[1]);bh=local(b[2],b[3])
 if bh[0]<bounds[0] or bl[0]>bounds[2] or bh[1]<bounds[1] or bl[1]>bounds[3]:continue
 g=transform(local,shape(sr.shape.__geo_interface__))
 if not g.is_valid:g=g.buffer(0)
 if g.intersects(query):
  q=g.intersection(study)
  if q.area>.05:roads.append(q);roadids.append(sr.record.as_dict().get('ROAD_ID'))
official=unary_union(roads);sw=[];swids=[]
for ft in json.load(open(a.sidewalks))['features']:
 g=transform(local,shape(ft['geometry']))
 if not g.is_valid:g=g.buffer(0)
 if g.intersects(study):
  q=g.intersection(study)
  if q.area>.05:sw.append(q);swids.append(ft['properties'].get('ID'))
walk=unary_union(sw);fallback=[];gaps=[];sections=collections.defaultdict(lambda:{'route_length_m':0,'uncovered_route_m':0,'ways':0})
for t,line in routes:
 missing=line.difference(official.buffer(.5));n=sections[t['name']];n['route_length_m']+=line.length;n['uncovered_route_m']+=missing.length;n['ways']+=1
 if missing.length>.1:
  lanes=t.get('lanes','');lanes=int(lanes) if str(lanes).isdigit() else (2 if t.get('oneway')=='yes' else 4)
  width=lanes*3.25
  gaps.append({'osm_id':str(t['osm_id']),'section':t['name'],'missing_centerline_m':missing.length,'estimated_width_m':width,'basis':'OSM lanes x 3.25m; missing lanes assumed 2 one-way or 4 two-way','status':'estimated road extent'})
  fallback.append(missing.buffer(width/2,cap_style=2,join_style=2))
est=unary_union(fallback).difference(official);pavement=official.difference(walk);est=est.difference(walk)
def parts(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return sum([parts(x) for x in getattr(g,'geoms',[])],[])
def mesh(g,z0,z1):
 vs=[];fs=[];area=0;lost=0
 for poly in parts(g):
  if poly.area<.001:continue
  poly=poly.simplify(.001,preserve_topology=True);ts=list(constrained_delaunay_triangles(poly).geoms);area+=poly.area;lost+=abs(poly.area-sum(t.area for t in ts))
  for t in ts:
   pts=list(t.exterior.coords)[:-1];i=len(vs);vs.extend([(*q,z0) for q in pts]+[(*q,z1) for q in pts]);fs.extend([(i+2,i+1,i),(i+3,i+4,i+5)])
  for ring in [poly.exterior]+list(poly.interiors):
   for aa,bb in zip(list(ring.coords),list(ring.coords)[1:]):
    i=len(vs);vs.extend([(*aa,z0),(*bb,z0),(*bb,z1),(*aa,z1)]);fs.append((i,i+1,i+2,i+3))
 assert lost<0.01,('area loss',lost)
 return {'vertices':vs,'faces':fs,'area_m2':area,'triangulation_area_loss_m2':lost}
# Curbs along road-facing boundary only; sampling filters back edges and crop edges.
carriage=unary_union([official,est]).difference(walk);curb=[]
from shapely.ops import substring
for poly in parts(walk):
 line=LineString(poly.exterior.coords)
 for k in range(math.ceil(line.length)):
  seg=substring(line,k+.003,min(k+.997,line.length))
  if seg.geom_type!='LineString' or seg.length<.08:continue
  mid=seg.interpolate(.5,normalized=True)
  if mid.distance(study.boundary)<.03:continue
  # A .2m outside strip must touch mapped/estimated carriageway.
  strip=seg.buffer(.2,cap_style=2).difference(walk)
  if strip.intersection(carriage).area<strip.area*.45:continue
  curb.extend(parts(seg.buffer(.15,cap_style=2,join_style=2).intersection(walk)))
curbg=unary_union(curb)
# Existing detailed pilot stays visible; avoid duplicate curbs in its documented crop.
pilot=box(*ll(121.52075,25.04750),*ll(121.52412,25.04818));curbg=curbg.difference(pilot)
result={'summary':{'ground_route_ways':len(routes),'sections':dict(sections),'official_road_records':len(roads),'sidewalk_records':len(sw),'official_road_surface_m2':pavement.area,'estimated_road_surface_m2':est.area,'sidewalk_area_m2':walk.area,'curb_parts_before_pilot_exclusion':len(curb),'bounds':bounds},'assumptions':{'road_top_local_z':0,'road_thickness_m':.25,'sidewalk_top_local_z':.15,'curb_top_local_z':.17,'curb_width_m':.15,'study_clip_radius_m':70,'note':'All Z and construction sizes estimated; historic official road polygons are not a current survey; fallback geometry separately tagged'},'fallbacks':gaps,'source_road_ids':roadids,'source_sidewalk_ids':swids,'meshes':{'GROUND_ROADS_OFFICIAL_XY':mesh(pavement,-.25,0),'GROUND_ROADS_ESTIMATED_GAPS':mesh(est,-.25,0),'GROUND_SIDEWALKS_OFFICIAL_XY':mesh(walk,0,.15),'GROUND_CURBS_ESTIMATED':mesh(curbg,0,.17)}}
(out/'ground_payload.json').write_text(json.dumps(result));checks={k:v for k,v in result.items() if k!='meshes'};checks['mesh_area_checks']={k:{a:b for a,b in v.items() if a not in ['vertices','faces']} for k,v in result['meshes'].items()};(out/'ground_check.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2));print(json.dumps(result['summary'],ensure_ascii=False))
