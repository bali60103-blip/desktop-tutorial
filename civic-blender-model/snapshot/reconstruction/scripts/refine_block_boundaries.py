import osmium,json,pathlib,math
from pyproj import Transformer
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'BlockFacades';reg=json.load(open(root/'registration.json'));f=reg['live_to_twd97'];ang=math.radians(f['rotation_degrees']);org=[reg['origin_epsg3826'][i]+f['translation'][i] for i in [0,1]];tf=Transformer.from_crs(4326,3826,always_xy=True);bbox=(121.501,25.032,121.630,25.069);roads=[]
def xy(lon,lat):
 x,y=tf.transform(lon,lat);x-=org[0];y-=org[1];return ((math.cos(ang)*x+math.sin(ang)*y)/f['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/f['scale'])
class H(osmium.SimpleHandler):
 def way(self,w):
  t=dict(w.tags);h=t.get('highway')
  if h not in {'primary','secondary','tertiary','residential','unclassified','living_street','pedestrian','trunk','primary_link','secondary_link','tertiary_link','trunk_link','service'} or t.get('tunnel','no')!='no':return
  if h=='service' and (t.get('service') in ['driveway','parking_aisle','drive-through'] or t.get('access')=='private'):return
  try:
   ll=[(n.lon,n.lat) for n in w.nodes]
   if len(ll)>1 and any(bbox[0]<=x<=bbox[2] and bbox[1]<=y<=bbox[3] for x,y in ll):roads.append({'osm_id':str(w.id),'tags':t,'xy':[xy(*p) for p in ll]})
  except:pass
H().apply_file('/Users/ktlu/Downloads/taiwan-260908.osm.pbf',locations=True,idx='flex_mem');(out/'source/streets_plan_boundaries.json').write_text(json.dumps(roads,ensure_ascii=False));print({'plan_street_boundaries':len(roads),'method':'Public road centerlines in plan, including elevated-road corridors and non-private non-parking service lanes. Crossing lines do not imply at-grade connectivity.'})
