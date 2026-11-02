"""Extract mapped ground street network and building areas for full frontage-block completion."""
import osmium,json,pathlib,math,time
from pyproj import Transformer
from shapely.geometry import Polygon,shape,LineString,box
from shapely.ops import transform
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'BlockFacades';out.mkdir(exist_ok=True);(out/'source').mkdir(exist_ok=True)
reg=json.load(open(root/'registration.json'));f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in [0,1]];tf=Transformer.from_crs(4326,3826,always_xy=True)
def xy(lon,lat):
 x,y=tf.transform(lon,lat);x-=org[0];y-=org[1];return ((math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale'])
bbox=(121.501,25.032,121.630,25.069);region=box(*bbox);factory=osmium.geom.GeoJSONFactory();roads=[];buildings=[];errors=[]
class Handler(osmium.SimpleHandler):
 def way(self,w):
  t=dict(w.tags);h=t.get('highway');allowed={'primary','secondary','tertiary','residential','unclassified','living_street','pedestrian','trunk','primary_link','secondary_link','tertiary_link','trunk_link'}
  if h not in allowed or t.get('bridge','no')!='no' or t.get('tunnel','no')!='no' or t.get('layer','0') not in ['0','']:return
  try:
   ll=[(n.lon,n.lat) for n in w.nodes]
   if len(ll)<2 or not any(bbox[0]<=x<=bbox[2] and bbox[1]<=y<=bbox[3] for x,y in ll):return
   roads.append({'osm_id':str(w.id),'tags':t,'xy':[xy(*p) for p in ll]})
  except Exception as e:errors.append({'type':'road','id':w.id,'error':str(e)})
 def area(self,a):
  t=dict(a.tags)
  if not (t.get('building') and t['building']!='no') and not (t.get('building:part') and t['building:part']!='no'):return
  try:
   rings=list(a.outer_rings())
   if not rings:return
   first=rings[0][0]
   if not (bbox[0]-.003<=first.lon<=bbox[2]+.003 and bbox[1]-.003<=first.lat<=bbox[3]+.003):return
   g=shape(json.loads(factory.create_multipolygon(a)))
   if not g.intersects(region):return
   g=transform(xy,g);buildings.append({'osm_id':('w' if a.from_way() else 'r')+str(a.orig_id()),'tags':t,'geometry':g.__geo_interface__})
  except Exception as e:errors.append({'type':'building','id':a.id,'error':str(e)})
h=Handler();h.apply_file('/Users/ktlu/Downloads/taiwan-260908.osm.pbf',locations=True,idx='flex_mem');(out/'source/streets.json').write_text(json.dumps(roads,ensure_ascii=False));(out/'source/buildings.json').write_text(json.dumps(buildings,ensure_ascii=False));r={'ground_street_ways':len(roads),'building_areas':len(buildings),'errors':errors,'bbox_wgs84':bbox,'crs':'Registered Blender live XY in metres','limitations':'Mapped features only; street blocks are centerline-enclosed proxies, not cadastral parcels. Private service drives excluded as block boundaries.'};(out/'source/extraction.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print({k:v for k,v in r.items() if k!='errors'});print('errors',len(errors))
