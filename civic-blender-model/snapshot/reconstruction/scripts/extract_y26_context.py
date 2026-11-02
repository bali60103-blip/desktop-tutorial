import osmium,json,pathlib
class H(osmium.SimpleHandler):
 def __init__(self):super().__init__();self.coords={};self.nodes=[];self.ways=[]
 def node(self,n):
  x,y=n.location.lon,n.location.lat
  if 121.5107<x<121.5124 and 25.0491<y<25.0504:
   self.coords[n.id]=[x,y]
   if n.tags:self.nodes.append({'id':n.id,'xy':[x,y],'tags':dict(n.tags)})
 def way(self,w):
  if not w.tags or not all(n.ref in self.coords for n in w.nodes):return
  t=dict(w.tags)
  if any(k in t for k in ['building','highway','man_made','indoor','barrier','railway','amenity']):self.ways.append({'id':w.id,'coords':[self.coords[n.ref] for n in w.nodes],'tags':t})
h=H();h.apply_file('/Users/ktlu/Downloads/taiwan-260908.osm.pbf');out=pathlib.Path('/tmp/civic-y26-context');out.mkdir(exist_ok=True);(out/'osm_context.json').write_text(json.dumps({'nodes':h.nodes,'ways':h.ways},ensure_ascii=False,indent=2));print(json.dumps({'nodes':len(h.nodes),'ways':len(h.ways),'steps':[w for w in h.ways if w['tags'].get('highway')=='steps']},ensure_ascii=False))
