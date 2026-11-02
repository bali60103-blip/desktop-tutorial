"""Supplement nearby OSM multipolygon building relations omitted by way-only extraction."""
import osmium,json,argparse
from pyproj import Transformer
p=argparse.ArgumentParser()
for n in ['pbf','osm','out']:p.add_argument('--'+n,required=True)
a=p.parse_args();d=json.load(open(a.osm));tr=Transformer.from_crs(4326,3826,always_xy=True);added=[]
class H(osmium.SimpleHandler):
 def area(self,area):
  if area.from_way() or 'building' not in area.tags:return
  for k,outer in enumerate(area.outer_rings()):
   ll=[(n.lon,n.lat) for n in outer]
   if not any(121.518<lon<121.527 and 25.045<lat<25.051 for lon,lat in ll):continue
   holes=[[(n.lon,n.lat) for n in inner] for inner in area.inner_rings(outer)]
   tags=dict(area.tags);tags['_source_type']='relation';tags['_source_relation_id']=str(area.orig_id());tags['_part_index']=str(k)
   added.append(dict(id=-(area.orig_id()*100+k),tags=tags,ll=ll,xy=[tr.transform(*q) for q in ll],holes_xy=[[tr.transform(*q) for q in ring] for ring in holes]))
H().apply_file(a.pbf,locations=True,idx='flex_mem')
d['ways'].extend(added);d['building_relation_supplement']={'count':len(added),'scope':'Zhonglin surroundings; not complete Taiwan building dataset'}
open(a.out,'w').write(json.dumps(d,ensure_ascii=False));print(json.dumps({'added':len(added),'relations':[(r['tags']['_source_relation_id'],r['tags'].get('name')) for r in added]},ensure_ascii=False))
