import osmium,json,pathlib,math,statistics,runpy,re
from pyproj import Transformer
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
from shapely import make_valid,set_precision
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'CompletionPass';tf=Transformer.from_crs(4326,3826,always_xy=True);ox,oy=301495.6087493267,2770459.509396812
controls=json.load(open('/tmp/civic-frontage-full/axis_controls.json'));axis=LineString([(r['twd97'][0]-ox,r['twd97'][1]-oy) for r in controls['crossings']]);existing=unary_union([Polygon(t['outer'],t['holes']) for r in json.load(open(out/'source/first_row.json'))['buildings'] for t in r['rings']]);added=[];flags=[]
class H(osmium.SimpleHandler):
 def area(self,area):
  if area.from_way() or 'building' not in area.tags:return
  for k,ring in enumerate(area.outer_rings()):
   ll=[(n.lon,n.lat) for n in ring]
   if not any(121.49<x<121.65 and 25.025<y<25.07 for x,y in ll):continue
   def xy(r):return [(tf.transform(n.lon,n.lat)[0]-ox,tf.transform(n.lon,n.lat)[1]-oy) for n in r]
   g=make_valid(Polygon(xy(ring),[xy(r) for r in area.inner_rings(ring)]))
   if g.is_empty or g.area<1 or g.distance(axis)>120:return
   overlap=g.intersection(existing).area/g.area
   if overlap>.8:return
   c=g.representative_point();a=axis.interpolate(axis.project(c));ray=LineString([a,c]);before=ray.difference(g.buffer(.1));blocked=before.intersection(existing.buffer(-.1)).length>.5
   if blocked:return
   tag=dict(area.tags);v=tag.get('height','').replace('m','').strip();h=float(v) if re.fullmatch(r'\d+(\.\d+)?',v) else None;status='OSM relation height tag; not surveyed'
   if not h:
    v=tag.get('building:levels','');h=float(v)*3.3 if re.fullmatch(r'\d+(\.\d+)?',v) else 13.2;status='ESTIMATED levels*3.3 or13.2m fallback; relation footprint'
   added.append({'name':'COMP_REL_'+str(area.orig_id())+'_'+str(k),'g':g,'height':h,'tags':tag,'status':status});flags.append({'id':'REL_'+str(area.orig_id())+'_'+str(k),'xy':[c.x,c.y],'type':'relation_height_and_frontage_pending','overlap_ratio':overlap,'tags':tag})
H().apply_file('/Users/ktlu/Downloads/taiwan-260908.osm.pbf',locations=True,idx='flex_mem')
mesh=runpy.run_path('/tmp/civic-stage00/reconstruction/scripts/prepare_mall_shells.py')['mesh'];parts=[]
for r in added:
 g=set_precision(r['g'],.0001)
 for i,q in enumerate([g] if g.geom_type=='Polygon' else g.geoms):
  if q.geom_type=='Polygon' and q.area>.001:parts.append({'name':r['name']+'_'+str(i),'mesh':mesh(q,0,r['height']),'status':r['status'],'tags':r['tags']})
(out/'relations_payload.json').write_text(json.dumps({'parts':parts,'issues':flags},ensure_ascii=False));print({'parts':len(parts),'relations':len(flags)})
