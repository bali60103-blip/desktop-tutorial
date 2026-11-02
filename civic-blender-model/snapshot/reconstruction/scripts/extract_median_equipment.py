"""Extract OSM surface-equipment candidates; absence in OSM is not absence on site."""
import osmium,json,pathlib
from shapely.geometry import shape,Point,LineString,mapping,Polygon
from shapely.ops import transform,unary_union
from pyproj import Transformer
OUT=pathlib.Path('/tmp/civic-median-equipment')
PBF='/Users/ktlu/Downloads/taiwan-260908.osm.pbf'
tf=Transformer.from_crs(4326,3826,always_xy=True).transform
roads=json.loads(pathlib.Path('/tmp/civic-stage01/civic_all_named_ways.geojson').read_text())
axis=unary_union([transform(tf,shape(f['geometry'])) for f in roads['features']])
def relevant(t):
 return t.get('man_made') in ['ventilation_shaft','street_cabinet','water_tower','chimney','pipeline'] or t.get('building') in ['service','transformer_tower'] or t.get('power') in ['substation','transformer'] or t.get('utility') in ['ventilation','sewerage','power']
class A(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.ways=[];self.ids=set();self.nodes=[]
 def node(self,n):
  if 121.49<n.location.lon<121.65 and 25.02<n.location.lat<25.07 and relevant(n.tags):
   self.nodes.append((n.id,dict(n.tags),[n.location.lon,n.location.lat]))
 def way(self,w):
  if relevant(w.tags):
   ns=[n.ref for n in w.nodes];self.ids.update(ns);self.ways.append((w.id,dict(w.tags),ns))
a=A();a.apply_file(PBF)
class B(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.xy={}
 def node(self,n):
  if n.id in a.ids:self.xy[n.id]=[n.location.lon,n.location.lat]
b=B();b.apply_file(PBF)
features=[]
def add(i,t,g,typ):
 d=axis.distance(transform(tf,g))
 if d<=70:features.append({'type':'Feature','geometry':mapping(g),'properties':{'osm_id':i,'osm_type':typ,**t,'distance_named_road_m':round(d,2),'status':'OSM candidate; median membership and surface visibility unverified'}})
for i,t,xy in a.nodes:add(i,t,Point(xy),'node')
for i,t,ns in a.ways:
 if not all(n in b.xy for n in ns):continue
 xy=[b.xy[n] for n in ns]
 if not xy or not (121.49<xy[0][0]<121.65 and 25.02<xy[0][1]<25.07):continue
 g=Polygon(xy) if len(xy)>=4 and xy[0]==xy[-1] else LineString(xy)
 add(i,t,g,'way')
(OUT/'osm_equipment_candidates.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False,indent=2))
print(json.dumps([f['properties'] for f in features],ensure_ascii=False,indent=2))
