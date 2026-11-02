"""Extract corridor OSM building candidates from local PBF without global node cache."""
import osmium,json,pathlib
from pyproj import Transformer
from shapely.geometry import Polygon
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934')
axis=json.load(open(root/'Cameras_500m/camera_stations.json'))['axis_twd97']
inv=Transformer.from_crs(3826,4326,always_xy=True);tf=Transformer.from_crs(4326,3826,always_xy=True)
xmin=min(p[0] for p in axis)-250;xmax=max(p[0] for p in axis)+250;ymin=min(p[1] for p in axis)-250;ymax=max(p[1] for p in axis)+250
ll=[inv.transform(x,y) for x in [xmin,xmax] for y in [ymin,ymax]];west=min(x for x,y in ll);east=max(x for x,y in ll);south=min(y for x,y in ll);north=max(y for x,y in ll)
class H(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.nodes={};self.rows=[];self.relations=[]
 def node(self,n):
  x,y=n.location.lon,n.location.lat
  if west<=x<=east and south<=y<=north:self.nodes[n.id]=[x,y]
 def way(self,w):
  if not w.tags.get('building') or w.tags.get('building')=='no':return
  ids=[n.ref for n in w.nodes]
  if len(ids)<4 or ids[0]!=ids[-1] or not all(i in self.nodes for i in ids):return
  xy=[tf.transform(*self.nodes[i]) for i in ids];g=Polygon(xy)
  if not g.is_valid or g.is_empty:return
  self.rows.append({'id':w.id,'tags':dict(w.tags),'xy':xy})
 def relation(self,r):
  if r.tags.get('building'):self.relations.append(r.id)
h=H();h.apply_file('/Users/ktlu/Downloads/taiwan-260908.osm.pbf')
out=pathlib.Path('/tmp/civic-frontage-full');out.mkdir(exist_ok=True)
(out/'osm_buildings.json').write_text(json.dumps({'ways':h.rows},ensure_ascii=False))
(out/'axis_controls.json').write_text(json.dumps({'crossings':[{'twd97':p} for p in axis]}))
report={'simple_building_ways':len(h.rows),'bbox_wgs84':[west,south,east,north],'coverage':'full analysis axis bbox; simple closed ways only','limitations':'Multipolygon building relations not assembled in this pass; omissions possible; no claims of complete building coverage.'}
(out/'extraction_check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
