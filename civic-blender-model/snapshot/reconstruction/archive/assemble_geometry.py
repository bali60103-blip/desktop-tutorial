import json, math, pathlib, shapefile
import numpy as np
from shapely.geometry import shape, Polygon, LineString, mapping, Point
from shapely.ops import unary_union, triangulate
from shapely import make_valid, constrained_delaunay_triangles
from pyproj import Transformer
P=pathlib.Path('/tmp/civic-rebuild')
reg=json.loads((P/'registration.json').read_text());origin=np.array(reg['origin_epsg3826'])+reg['live_to_twd97']['translation'];sc=reg['live_to_twd97']['scale'];a=math.radians(reg['live_to_twd97']['rotation_degrees']);R=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
def local(c):return ((np.array(c)[:,:2]-origin)@R/sc).tolist()
tr=Transformer.from_crs(4326,3826,always_xy=True)
geo=json.load(open('/Users/ktlu/Downloads/市民大道全長.geojson'))
axis=unary_union([LineString([tr.transform(*p[:2]) for p in f['geometry']['coordinates']]) for f in geo['features']]);clip=axis.buffer(120)
ways=json.loads((P/'osm.json').read_text())['ways'];out=[];features=[];counts={}
def polygons(g):
 if g.geom_type=='Polygon':yield g
 elif hasattr(g,'geoms'):
  for s in g.geoms:yield from polygons(s)
def mesh(name,g,z0,z1,layer,props):
 g=make_valid(g);vv=[];ff=[]
 for p in polygons(g):
  if p.area<0.015:continue
  p=p.simplify(.035,preserve_topology=True)
  lookup={}
  def vert(c,z):
   key=(round(c[0],5),round(c[1],5),z)
   if key not in lookup:
    xy=local([c])[0];lookup[key]=len(vv);vv.append([*xy,z])
   return lookup[key]
  for t in constrained_delaunay_triangles(p).geoms:
   cs=list(t.exterior.coords)[:3];ids=[vert(c,z1) for c in cs];ff.append(ids)
   if z1!=z0:ff.append([vert(c,z0) for c in reversed(cs)])
  if z1!=z0:
   for ring in [p.exterior,*p.interiors]:
    cs=list(ring.coords)
    for u,v in zip(cs,cs[1:]):ff.append([vert(u,z0),vert(v,z0),vert(v,z1),vert(u,z1)])
 if vv:
  out.append(dict(name=name,vertices=vv,faces=ff,layer=layer,props=props));counts[layer]=counts.get(layer,0)+1
  features.append(dict(type='Feature',geometry=mapping(g),properties=dict(name=name,layer=layer,**props)))
sw=[]
for f in json.loads((P/'taipei-sidewalks.geojson').read_text())['features']:
 g=shape(f['geometry'])
 if not g.intersects(clip):continue
 g=make_valid(g).intersection(clip);sw.append(g);pr=f['properties']
 mesh('SW_'+pr['ID']+'_'+pr['NAME_Road'],g,0,.15,'01_Sidewalks_official_XY',dict(source='Taipei sidewalk GIS 2026-01-14',source_id=pr['ID'],road=pr['NAME_Road'],width_attribute=pr['SW_WTH_ItemValue'],confidence='Official XY; curb elevation +0.15 m assumed; not current field survey'))
swunion=unary_union(sw)
roads=[]
for s in shapefile.Reader(str(P/'roads/8mroadup/Road.shp')).iterShapeRecords():
 g=shape(s.shape.__geo_interface__)
 if not g.intersects(clip):continue
 pr=s.record.as_dict();g=make_valid(g).intersection(clip);roads.append(g)
 mesh('RD_'+str(pr['OBJECTID'])+'_'+str(pr['ROADNAME']),g.difference(swunion),-.12,0,'02_Roads_official_extent',dict(source='Taipei road survey 2014–2016; file updated 2025-09-17',source_id=pr['OBJECTID'],road=pr['ROADNAME'],road_width_attribute=pr['ROADWIDTH'],median_area_attribute=pr['CEN_MEDIAN'],confidence='Survey road extent minus separate sidewalk GIS; not verified carriageway edge; flat datum Z=0'))
for w in ways:
 if w['tags'].get('footway')=='traffic_island':
  g=LineString(w['xy'])
  if g.intersects(clip):mesh('ISLAND_OSM_'+str(w['id']),g.buffer(.75,cap_style=2),0,.15,'03_Islands_estimated_width',dict(source='OSM footway=traffic_island',osm_id=w['id'],confidence='Mapped path location; 1.5 m island width and 0.15 m height assumed, not actual outline'))
# Main elevated geometry uses each mapped direction, variable width inferred from lanes.
decks=[]
for w in ways:
 t=w['tags']
 if t.get('highway')!='trunk' or '市民大道高架' not in t.get('name',''):continue
 line=LineString(w['xy']);lanes=int(t.get('lanes','2'));width=lanes*3.25+2.0;deck=line.buffer(width/2,cap_style=2,join_style=2);decks.append(deck)
 prop=dict(source='OSM centerline; engineering form guided by CECI 2014',osm_id=w['id'],lanes=lanes,width_m=width,confidence='XY centerline mapped; width=lanes*3.25+2, elevation 8m and member dimensions estimated; layer tag is not elevation')
 mesh('DECK_'+str(w['id']),deck,7.65,8,'04_Elevated_deck_estimated',prop)
 for side in [-1,1]:
  rail=line.offset_curve(side*(width/2-.2),join_style=2)
  mesh('PARAPET_'+str(w['id'])+'_'+str(side),rail.buffer(.16,cap_style=2),8,9.1,'05_Parapets_estimated',prop)
 # I section steel girders: two flanges and a slender web, not a solid deep slab.
 for k in range(4):
  off=(k-1.5)*width/4;girder=line.offset_curve(off,join_style=2)
  for suffix,half,z0,z1 in [('web',.035,5.65,7.60),('bottom',.24,5.60,5.68),('top',.24,7.57,7.65)]:mesh('GIRDER_'+str(w['id'])+'_'+str(k)+'_'+suffix,girder.buffer(half,cap_style=2),z0,z1,'06_Steel_girders_estimated',prop)
deckunion=unary_union(decks)
# Preserve prior column hypotheses visibly as amber, never relabel as surveyed supports.
inv=json.load(open('/tmp/civic-live-inventory.json'))['result']
for o in inv['objects']:
 if not o['name'].startswith('Pier_'):continue
 xy=(np.array(o['location'][:2])@R.T)*sc+origin;pt=Point(xy)
 if deckunion.covers(pt):
  g=pt.buffer(1,cap_style=3)
  mesh('UNVERIFIED_'+o['name'],g,0,5.60,'07_Piers_legacy_UNVERIFIED',dict(source='Previous scene interpolated support',confidence='UNVERIFIED XY and dimensions. NOT surveyed pier location; retained as hypothesis',legacy_name=o['name']))
for f in json.loads((P/'civic-official-pier-polygons.geojson').read_text())['features']:
 mesh('CANDIDATE_'+str(f['properties'].get('OBJECTID','')),shape(f['geometry']),.16,.30,'08_Official_column_candidates_HIDDEN',dict(source='Taipei sidewalk facility inventory; class 墩柱',confidence='Official footprint, identity as bridge pier NOT established'))
# Existing median is retained separately by Blender script until a surveyed median layer exists.
payload=dict(objects=out,counts=counts,registration=reg,local_origin=origin.tolist(),bounds_local=local([[axis.bounds[0],axis.bounds[1]],[axis.bounds[2],axis.bounds[3]]]))
(P/'build_payload.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')))
(P/'rebuild_features_TWD97.geojson').write_text(json.dumps(dict(type='FeatureCollection',crs=dict(type='name',properties=dict(name='urn:ogc:def:crs:EPSG::3826')),features=features),ensure_ascii=False))
print(json.dumps(dict(counts=counts,objects=len(out),vertices=sum(len(o['vertices']) for o in out),bounds=payload['bounds_local']),ensure_ascii=False))
