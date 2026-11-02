"""Taipei Station vent group: photograph-informed shell; all dimensions estimated."""
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

ids=['w552658460','w552658461','w552658462','w552658463'];rows=json.load(open(out/'corrected_rows_context.json'));items=[]
for r in rows:
 if r['osm_id'] not in ids:continue
 p=orient(shape(r['geometry']).geoms[0],1);pieces=[];height=7.2
 for name,poly,z0,z1,mat in [('BASE',p,0,.15,'STONE'),('ROOF',p,7.0,7.2,'STONE')]:
  vs,fs=extrude(poly,z0,z1);pieces.append({'name':name,'vertices':vs,'faces':fs,'material':mat})
 coords=list(p.exterior.coords)
 for edge,(a,b) in enumerate(zip(coords,coords[1:])):
  dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);d=(dx/L,dy/L);n=(d[1],-d[0]);holes=[];louvers=[]
  if L>8:
   for c in [.28,.72]:louvers.append(box(c*L-L*.16,4.5,c*L+L*.16,6.6))
  elif L>3:louvers.append(box(L*.14,4.5,L*.86,6.6))
  holes.extend(louvers);door=None
  if n[0]>.9 and L>3 and L<8:
   c=L*.72;door=box(c-.55,.15,c+.55,2.25);holes.append(door)
  wall=box(0,.15,L,7.)
  for h in holes:wall=wall.difference(h)
  def component(label,poly,lo,hi,mat):
   vs,fs=extrude(poly,lo,hi)
   if vs:pieces.append({'name':str(edge)+'_'+label,'vertices':[[a[0]+d[0]*s+n[0]*w,a[1]+d[1]*s+n[1]*w,z] for s,z,w in vs],'faces':fs,'material':mat})
  component('WALL',wall,-.25,0,'STONE')
  for j,h in enumerate(louvers):
   x0,z0,x1,z1=h.bounds
   for k in range(14):component('LOUVER_'+str(j)+'_'+str(k),box(x0+.05,z0+.08+k*.14,x1-.05,z0+.14+k*.14),-.12,-.035,'METAL')
   for k,f in enumerate([box(x0-.04,z0,x0+.04,z1),box(x1-.04,z0,x1+.04,z1),box(x0,z0-.04,x1,z0+.04),box(x0,z1-.04,x1,z1+.04),box((x0+x1)/2-.03,z0,(x0+x1)/2+.03,z1)]):component('FRAME_'+str(j)+'_'+str(k),f,-.02,.03,'METAL')
  if door:
   x0,z0,x1,z1=door.bounds;component('DOOR_LEAF',box(x0+.04,z0+.02,x1-.04,z1-.04),-.10,-.04,'DOOR')
   for k,f in enumerate([box(x0-.04,z0,x0+.04,z1),box(x1-.04,z0,x1+.04,z1),box(x0,z1-.04,x1,z1+.04)]):component('DOOR_FRAME_'+str(k),f,-.02,.03,'METAL')
   component('DOOR_HANDLE',box(x0+.13,1.0,x0+.16,1.3),.015,.07,'METAL')
  for z in [2.5,3.2,3.7]:
   q=box(.15,z-.01,L-.15,z+.01)
   for h in holes:q=q.difference(h.buffer(.03))
   component('REVEAL_'+str(z),q,.001,.004,'JOINT')
 items.append({'osm_id':r['osm_id'],'pieces':pieces,'height_m':height,'prior_height_m':r['height_m'],'height_uncertainty_m':1.5,'observed_group_member':r['osm_id']!='w552658463'})
for row in items:
 for m in row['pieces']:
  edges={}
  for f in m['faces']:
   for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
  assert all(v==2 for v in edges.values()),m['name']
r={'items':items,'source_url':'https://www.google.com/maps/@25.047999,121.5160201,3a,90y,270h,90t/data=!3m4!1e1!3m2!1sqKQ4Ga927cEaDMDG_3GRKg!2e0','imagery_date':'2025-03','scope':'Three adjacent shafts visually observed: concrete/stone rectangular shells, upper localized louvers, low metal service door; fourth shaft extrapolated from group. Heights7.2m +/-1.5m, openings, door sizes and hidden faces remain estimates. Train graphics omitted. Not surveyed or current-condition certification.'};(out/'station_vent_photo_payload.json').write_text(json.dumps(r,ensure_ascii=False));print({'shafts':len(items),'pieces':sum(len(x['pieces']) for x in items)})
