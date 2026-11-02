"""Create approximate parking section envelopes from official road limits, not survey plans."""
import json,math,pathlib
from shapely.geometry import LineString,Point,Polygon
from shapely.ops import unary_union,nearest_points,substring
from shapely import constrained_delaunay_triangles
from pyproj import Transformer
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934')
axis=LineString(json.load(open(root/'Cameras_500m/camera_stations.json'))['axis_twd97'])
ways=json.load(open('/tmp/civic-stage05/osm_with_relations.json'))['ways']
reg=json.load(open('/tmp/civic-rebuild/registration.json'));cfg=reg['live_to_twd97'];ang=math.radians(cfg['rotation_degrees']);org=[reg['origin_epsg3826'][i]+cfg['translation'][i] for i in range(2)]
def local(p):
 x,y=p[0]-org[0],p[1]-org[1];return [(math.cos(ang)*x+math.sin(ang)*y)/cfg['scale'],(-math.sin(ang)*x+math.cos(ang)*y)/cfg['scale']]
def road(name):return unary_union([LineString(w['xy']) for w in ways if w['tags'].get('name')==name and 'highway' in w['tags']])
controls={}
for name in ['公園路','中山北路一段','林森北路','金山北路','建國南路一段','復興南路一段','敦化南路一段','延吉街']:
 r=road(name);a,b=nearest_points(axis,r);controls[name]={'station':axis.project(a),'distance_m':a.distance(b),'xy':list(a.coords)[0]}
troad=road('鄭州路');ta=nearest_points(troad,road('西寧北路'))[0];tb=nearest_points(troad,road('塔城街'))[0];tax=LineString([ta,tb])
sections=[('塔城',None,None,2),('公中','公園路','中山北路一段',2),('中林','中山北路一段','林森北路',2),('林金','林森北路','金山北路',2),('建復','建國南路一段','復興南路一段',1),('復敦','復興南路一段','敦化南路一段',2),('敦延','敦化南路一段','延吉街',2),('延吉','延吉街',None,1)]
tf=Transformer.from_crs(4326,3826,always_xy=True)
entrances=[f for f in json.load(open('/tmp/civic-stage01/entrance_candidates.geojson'))['features'] if f['properties'].get('amenity')=='parking_entrance']
rows=[]
for name,start,end,levels in sections:
 if name=='塔城':line=tax;extent_note='Straight working chord between mapped Zhengzhou-road cross-street controls'
 elif name=='延吉':
  s=controls[start]['station'];line=substring(axis,max(0,s-100),min(axis.length,s+100));extent_note='Assumed 100m each side of Yanji; not published footprint length'
 else:
  a,b=sorted([controls[start]['station'],controls[end]['station']]);line=substring(axis,a+min(15,(b-a)/10),b-min(15,(b-a)/10));extent_note='Official road section; assumed end setback 15m; not measured footprint'
 if line.length<5:raise ValueError((name,line.length,controls))
 poly=line.buffer(12,cap_style='flat',join_style='mitre')
 # reserve a schematic central interlevel opening, explicitly separate from real plan locations
 holes=[]
 if levels==2 and line.length>100:
  mid=line.length/2;a=line.interpolate(mid-18);b=line.interpolate(mid+18);hole=LineString([a,b]).buffer(2.1,cap_style='flat');holes=[hole]
 selected=[]
 for f in entrances:
  p=Point(tf.transform(*f['geometry']['coordinates']))
  if p.distance(line)<40:
   selected.append({'osm_id':f['properties']['osm_id'],'xy':local(p.coords[0]),'distance_to_section_m':p.distance(line),'status':'OSM parking entrance candidate, association to section unverified'})
 rows.append({'name':name,'levels':levels,'length_m':line.length,'width_assumed_m':24,'axis_live':[local(p) for p in line.coords],'outline':[local(p) for p in poly.exterior.coords],'floor_polygons':{str(k):[[local(p) for p in (poly.difference(unary_union(holes)) if k==1 and holes else poly).exterior.coords]] for k in []},'interlevel_hole':[[local(p) for p in h.exterior.coords] for h in holes],'entrances':selected,'extent_status':extent_note})
out=pathlib.Path('/tmp/civic-parking-segments');out.mkdir(exist_ok=True)
(out/'sections.json').write_text(json.dumps({'controls':controls,'sections':rows,'source_sections_url':'https://pma.gov.taipei/News_Content.aspx?n=DDE3C27CE0E27008&s=3AE32F7149F0D6CF&sms=B12D05A2F2C8370E','assumptions':'24m width; -3.6m per level; source-confirmed floor count; outlines are comparative envelopes only.'},ensure_ascii=False,indent=2))
print(json.dumps({'controls':controls,'sections':[{'name':r['name'],'length':r['length_m'],'levels':r['levels'],'entry_candidates':len(r['entrances'])} for r in rows]},ensure_ascii=False))
