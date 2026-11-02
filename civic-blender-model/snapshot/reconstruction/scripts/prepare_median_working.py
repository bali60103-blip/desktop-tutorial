"""Estimate median strips only inside official records with nonzero median area.
Position from opposing OSM carriageways; openings around mapped crossing nodes.
"""
import json,math,re,pathlib,argparse
import shapefile
from shapely.geometry import shape,LineString,Point,Polygon
from shapely.ops import unary_union,transform
from shapely import constrained_delaunay_triangles, set_precision
from pyproj import Transformer
p=argparse.ArgumentParser()
for n in ['routes','roads','crossings','registration','out']:p.add_argument('--'+n,required=True)
a=p.parse_args();reg=json.load(open(a.registration));f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in (0,1)];tr=Transformer.from_crs(4326,3826,always_xy=True)
def loc(x,y,z=None):
 x,y=x-org[0],y-org[1];return ((math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale'])
routes=[]
for ft in json.load(open(a.routes))['features']:
 t=ft['properties']
 if re.fullmatch('市民大道[一二三四五六七八]段',t.get('name','')) and t.get('bridge')!='yes' and t.get('oneway')=='yes':routes.append((t,LineString([loc(*tr.transform(*q)) for q in ft['geometry']['coordinates']])))
axis=unary_union([l for t,l in routes]);known=[]
for sr in shapefile.Reader(a.roads).iterShapeRecords():
 r=sr.record.as_dict()
 if not r.get('CEN_MEDIAN') or r['CEN_MEDIAN']<=0:continue
 g=transform(loc,shape(sr.shape.__geo_interface__))
 if not g.is_valid:g=g.buffer(0)
 if g.distance(axis)<5:known.append(g)
allowed=unary_union(known)
def tangent(line,s):
 aa=line.interpolate(max(0,s-.5));bb=line.interpolate(min(line.length,s+.5));dx,dy=bb.x-aa.x,bb.y-aa.y;d=math.hypot(dx,dy);return (dx/d,dy/d) if d else (1,0)
def width(t):
 n=t.get('lanes','');return (int(n) if str(n).isdigit() else 2)*3.25
patches=[];wide=0
for t,line in routes:
 for k in range(int(line.length/5)+1):
  s=min(k*5,line.length);p0=line.interpolate(s)
  if not allowed.covers(p0):continue
  v=tangent(line,s);choices=[]
  for other,l2 in routes:
   if other['osm_id']==t['osm_id'] or other['name']!=t['name']:continue
   q=l2.interpolate(l2.project(p0));dist=p0.distance(q)
   if not 4<dist<45:continue
   u=tangent(l2,l2.project(p0))
   if u[0]*v[0]+u[1]*v[1]>-.6:continue
   choices.append((dist,other,q))
  if not choices:continue
  dist,other,q=min(choices,key=lambda x:x[0]);gap=dist-(width(t)+width(other))/2
  if gap>12:wide+=1
  if gap<.6:continue
  n=((q.x-p0.x)/dist,(q.y-p0.y)/dist);aa=(p0.x+n[0]*width(t)/2,p0.y+n[1]*width(t)/2);bb=(q.x-n[0]*width(other)/2,q.y-n[1]*width(other)/2)
  if gap>12:
   center=((aa[0]+bb[0])/2,(aa[1]+bb[1])/2);aa=(center[0]-n[0]*6,center[1]-n[1]*6);bb=(center[0]+n[0]*6,center[1]+n[1]*6)
  patch=Polygon([(aa[0]-v[0]*2.5,aa[1]-v[1]*2.5),(aa[0]+v[0]*2.5,aa[1]+v[1]*2.5),(bb[0]+v[0]*2.5,bb[1]+v[1]*2.5),(bb[0]-v[0]*2.5,bb[1]-v[1]*2.5)])
  if patch.is_valid:patches.append(patch)
median=unary_union(patches).intersection(allowed);cuts=unary_union([Point(loc(*r['twd97'])).buffer(14) for r in json.load(open(a.crossings))['crossings'] if r['distance_to_ground_route_m']<2]);median=median.difference(cuts).buffer(-.01).buffer(.01)
crosspoints=[Point(loc(*r['twd97'])) for r in json.load(open(a.crossings))['crossings'] if r['distance_to_ground_route_m']<2]
links=[LineString([a,b]).buffer(6) for i,a in enumerate(crosspoints) for b in crosspoints[i+1:] if 2<a.distance(b)<45]
median=median.difference(unary_union(links))
median=set_precision(median.simplify(.02,preserve_topology=True),.01)
def parts(g):
 if g.is_empty:return []
 if g.geom_type=='Polygon':return [g]
 return sum([parts(x) for x in getattr(g,'geoms',[])],[])
vs=[];fs=[]
for poly in parts(median):
 if poly.area<.4:continue
 for tri in constrained_delaunay_triangles(poly).geoms:
  pts=list(tri.exterior.coords)[:-1];i=len(vs);vs.extend([(*q,0) for q in pts]+[(*q,.18) for q in pts]);fs.extend([(i+2,i+1,i),(i+3,i+4,i+5)])
 for ring in [poly.exterior]+list(poly.interiors):
  coords=list(ring.coords)
  for aa,bb in zip(coords,coords[1:]):
   i=len(vs);vs.extend([(*aa,0),(*bb,0),(*bb,.18),(*aa,.18)]);fs.append((i,i+1,i+2,i+3))
r={'summary':{'median_working_area_m2':median.area,'median_components':len(parts(median)),'official_records_with_median_area':len(known),'wide_gap_samples_capped_at_12m':wide},'assumptions':{'height_m':.18,'max_gap_width_m':12,'crossing_clearance_radius_m':14,'lane_width_m':3.25,'status':'Estimated median location; official CEN_MEDIAN confirms area attribute only, not geometry'},'mesh':{'vertices':vs,'faces':fs}}
out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True);(out/'median_payload.json').write_text(json.dumps(r));(out/'median_check.json').write_text(json.dumps({k:v for k,v in r.items() if k!='mesh'},ensure_ascii=False,indent=2));print(json.dumps(r['summary']))
