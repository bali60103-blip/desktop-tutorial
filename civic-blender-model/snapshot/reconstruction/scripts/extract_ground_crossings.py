"""Extract explicitly mapped OSM crossing nodes near full Civic Blvd ground routes."""
import osmium,json,argparse,re
from shapely.geometry import LineString,Point
from shapely.ops import unary_union
from pyproj import Transformer
p=argparse.ArgumentParser()
for n in ['pbf','routes','out']:p.add_argument('--'+n,required=True)
a=p.parse_args();tr=Transformer.from_crs(4326,3826,always_xy=True);fs=json.load(open(a.routes))['features'];ls=[LineString([tr.transform(*q) for q in f['geometry']['coordinates']]) for f in fs if re.fullmatch('市民大道[一二三四五六七八]段',f['properties'].get('name','')) and f['properties'].get('bridge')!='yes'];axis=unary_union(ls);rows=[]
class H(osmium.SimpleHandler):
 def node(self,n):
  if n.tags.get('highway')!='crossing':return
  if not n.location.valid():return
  x,y=tr.transform(n.location.lon,n.location.lat);dist=axis.distance(Point(x,y))
  if dist<=25:rows.append({'osm_id':str(n.id),'wgs84':[n.location.lon,n.location.lat],'twd97':[x,y],'tags':dict(n.tags),'distance_to_ground_route_m':dist})
H().apply_file(a.pbf);open(a.out,'w').write(json.dumps({'crossings':rows,'status':'Mapped crossing points; orientation and marking extents must be modeled as estimates'},ensure_ascii=False,indent=2));print(json.dumps({'mapped_crossing_nodes':len(rows)}))
