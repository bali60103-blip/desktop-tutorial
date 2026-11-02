"""Physical paving and curb pilot. Official XY; construction dimensions explicit estimates.
No inferred stair/ramp openings. Real openings preserved; artificial crop boundaries excluded from curbs.
"""
import argparse,json,pathlib,math
from shapely.geometry import shape,box,LineString,Point,Polygon
from shapely.ops import unary_union,substring,triangulate
from shapely import affinity,constrained_delaunay_triangles
from pyproj import Transformer
p=argparse.ArgumentParser()
for n in ['sidewalks','osm','registration','out']:p.add_argument('--'+n,required=True)
p.add_argument('--ramp-cut');a=p.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True);reg=json.load(open(a.registration));f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in (0,1)];tr=Transformer.from_crs(4326,3826,always_xy=True)
def loc(x,y,z=None):
 x,y=x-org[0],y-org[1];return ((math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale'])
from shapely.ops import transform
lo=loc(*tr.transform(121.52075,25.04750));hi=loc(*tr.transform(121.52412,25.04818));extent=box(*lo,*hi)
polys=[];sources=[]
for ft in json.load(open(a.sidewalks))['features']:
 if ft['properties'].get('NAME_Road')!='市民大道二段':continue
 g=transform(loc,shape(ft['geometry']))
 if not g.is_valid:g=g.buffer(0)
 if g.intersects(extent):polys.append(g);sources.append(ft['properties']['ID'])
g=unary_union(polys).intersection(extent)
from shapely import wkt
rampcut=wkt.loads(pathlib.Path(a.ramp_cut).read_text()) if a.ramp_cut else Polygon()
precut_area=g.area;g=g.difference(rampcut);ramp_removed=precut_area-g.area;assert g.area>100
ways=json.load(open(a.osm))['ways'];road=unary_union([LineString([loc(*q) for q in w['xy']]) for w in ways if w['tags'].get('name')=='市民大道二段' and w['tags'].get('bridge')!='yes'])
def pieces(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return [q for q in getattr(g,'geoms',[]) if q.geom_type=='Polygon' and q.area>1e-7]
curbs=[]
for poly in pieces(g):
 line=LineString(poly.exterior.coords)
 for k in range(math.ceil(line.length)):
  seg=substring(line,k+.003,min(k+.997,line.length))
  if seg.geom_type!='LineString' or seg.length<.04:continue
  mid=seg.interpolate(.5,normalized=True)
  if mid.distance(extent.boundary)<.02 or (not rampcut.is_empty and mid.distance(rampcut)<.03):continue
  aa=seg.interpolate(.4,normalized=True);bb=seg.interpolate(.6,normalized=True);dx,dy=bb.x-aa.x,bb.y-aa.y;norm=math.hypot(dx,dy)
  if norm<1e-8:continue
  q1=Point(mid.x-dy/norm*.1,mid.y+dx/norm*.1);q2=Point(mid.x+dy/norm*.1,mid.y-dx/norm*.1)
  inside,outside=(q1,q2) if g.contains(q1) else (q2,q1)
  if road.distance(outside)>=road.distance(inside)-.01:continue
  curbs.extend(pieces(seg.buffer(.15,cap_style=2,join_style=2).intersection(g)))
curb_union=unary_union(curbs);pave=g.difference(curb_union)
# Paving aligned to local pilot axis; no claim about actual bond pattern.
rotation=-4.6;rot=affinity.rotate(pave,-rotation,origin=(0,0));xmin,ymin,xmax,ymax=rot.bounds;tiles=[]
for j in range(math.floor(ymin/.3),math.ceil(ymax/.3)):
 offset=.3 if j%2 else 0
 for i in range(math.floor((xmin-offset)/.6),math.ceil((xmax-offset)/.6)):
  cell=box(i*.6+offset+.003,j*.3+.003,(i+1)*.6+offset-.003,(j+1)*.3-.003)
  if not rot.intersects(cell):continue
  for q in pieces(rot.intersection(cell)):
   if q.area>.0001:tiles.append(affinity.rotate(q,rotation,origin=(0,0)))
def mesh(polygons,z0,z1):
 vs=[];fs=[];err=0
 for poly in polygons:
  poly=poly.simplify(0.00001,preserve_topology=True)
  ts=list(constrained_delaunay_triangles(poly).geoms);err+=abs(sum(t.area for t in ts)-poly.area)
  for t in ts:
   coords=list(t.exterior.coords)[:-1];n=len(vs);vs.extend([(x,y,z0) for x,y in coords]+[(x,y,z1) for x,y in coords]);fs.extend([(n+2,n+1,n),(n+3,n+4,n+5)])
  for ring in [poly.exterior]+list(poly.interiors):
   pts=list(ring.coords)
   for aa,bb in zip(pts,pts[1:]):
    n=len(vs);vs.extend([(*aa,z0),(*bb,z0),(*bb,z1),(*aa,z1)]);fs.append((n,n+1,n+2,n+3))
 assert err<.01,('triangulation lost area',err)
 return {'vertices':vs,'faces':fs,'area_error_m2':err}
params={'curb_width_m':.15,'curb_top_z_m':.17,'tile_size_m':[.6,.3],'tile_thickness_m':.02,'tile_bottom_z_m':.15,'joint_m':.006,'bond_rotation_degrees':rotation,'status':'ESTIMATED construction dimensions; ground datum assumed; NOT field-verified'}
result={'parameters':params,'source_ids':sources,'summary':{'source_features':len(polys),'sidewalk_union_area_m2':g.area,'overlap_removed_m2':sum(q.intersection(extent).area for q in polys)-precut_area,'ramp_cut_area_m2':ramp_removed,'curb_stones':len(curbs),'paving_tiles':len(tiles),'curb_area_m2':curb_union.area,'tile_area_m2':sum(t.area for t in tiles)},'meshes':{'CURB_STONES_ESTIMATED':mesh(curbs,0,.17),'PAVING_TILES_ESTIMATED':mesh(tiles,.15,.17)}}
(out/'detail_payload.json').write_text(json.dumps(result));(out/'parameters_and_check.json').write_text(json.dumps({k:v for k,v in result.items() if k!='meshes'},ensure_ascii=False,indent=2));print(json.dumps(result['summary']))
