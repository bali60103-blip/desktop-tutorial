"""Recessed tile-faced shaft from 2024 street-view proportions; dimensions estimated."""
import json,os,pathlib,math
from shapely.geometry import shape,box,Polygon
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3'
def extrude(poly,z0,z1):
 vs=[];fs=[];lookup={}
 def idx(x,y,z):
  key=(round(x,6),round(y,6),round(z,6))
  if key not in lookup:lookup[key]=len(vs);vs.append(list(key))
  return lookup[key]
 for p in list(poly.geoms) if hasattr(poly,'geoms') else [poly]:
  if p.is_empty or p.geom_type!='Polygon':continue
  p=orient(p,1)
  for t in constrained_delaunay_triangles(p).geoms:
   co=list(orient(t,1).exterior.coords)[:-1];fs.extend([[idx(x,y,z1) for x,y in co],[idx(x,y,z0) for x,y in reversed(co)]])
  for ring in [p.exterior,*p.interiors]:
   co=list(ring.coords)
   for a,b in zip(co,co[1:]):fs.append([idx(*a,z0),idx(*b,z0),idx(*b,z1),idx(*a,z1)])
 return vs,fs


r=next(x for x in json.load(open(out/'corrected_rows_context.json')) if x['osm_id']=='w1015817093');p=orient(shape(r['geometry']).geoms[0],1);pieces=[]
for name,z0,z1 in [('BASE',0,.08),('ROOF',5.85,6.0)]:
 vs,fs=extrude(p,z0,z1);pieces.append({'name':name,'vertices':vs,'faces':fs,'material':'STONE'})
coords=list(p.exterior.coords)
for edge,(a,b) in enumerate(zip(coords,coords[1:])):
 dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);d=(dx/L,dy/L);n=(d[1],-d[0]);front=n[1]<-.8
 def component(label,poly,lo,hi,mat):
  vs,fs=extrude(poly,lo,hi)
  if vs:pieces.append({'name':str(edge)+'_'+label,'vertices':[[a[0]+d[0]*s+n[0]*w,a[1]+d[1]*s+n[1]*w,z] for s,z,w in vs],'faces':fs,'material':mat})
 wall=box(0,.08,L,5.85);recess=box(.43,.08,L-.43,4.65) if front else None
 if recess:
  wall=wall.difference(recess);component('RECESSED_PANEL',recess,-.23,-.12,'STONE')
 component('WALL',wall,-.25,0,'STONE')
 # Actual shallow reveal plus modeled mortar grid, spacing assumed from image.
 for k in range(1,math.ceil(L/.18)):
  q=box(k*.18-.006,.08,k*.18+.006,5.85)
  if recess:component('RECESSED_VERTICAL_'+str(k),q.intersection(recess),-.119,-.116,'JOINT');q=q.difference(recess)
  component('VERTICAL_'+str(k),q,.001,.004,'JOINT')
 for k in range(1,60):
  q=box(0,k*.10-.005,L,k*.10+.005)
  if recess:component('RECESSED_HORIZONTAL_'+str(k),q.intersection(recess),-.119,-.116,'JOINT');q=q.difference(recess)
  component('HORIZONTAL_'+str(k),q,.001,.004,'JOINT')
for m in pieces:
 edges={}
 for f in m['faces']:
  for a,b in zip(f,f[1:]+f[:1]):key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
 assert all(v==2 for v in edges.values()),m['name']
payload={'osm_id':r['osm_id'],'pieces':pieces,'prior_height_m':13.2,'total_height_estimate_m':6.0,'uncertainty_m':.8,'source_url':'https://www.google.com/maps/@25.047398,121.5159254,3a,90y,90t/data=!3m4!1e1!3m2!1sYLlXT-vhr7bk1pmnyTj4hQ!2e0','imagery_date':'2024-12','scope':'Visible tile-faced vertical shaft with recessed solid front panel, not an all-louver tower. Approximate6m height estimated from image width/height proportions against3.3m mapped frontage; perspective, datum, recess and tile module unmeasured. Adjacent low entry structure is outside this footprint and not inferred as part of shaft.'};(out/'tiled_shaft_photo_payload.json').write_text(json.dumps(payload,ensure_ascii=False));print({'parts':len(pieces),'height':6.0})
