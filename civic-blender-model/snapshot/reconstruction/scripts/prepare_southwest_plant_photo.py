"""Southwest station mechanical enclosure: observed exterior, estimated dimensions."""
import json,os,pathlib,math
from shapely.geometry import shape,box,Polygon,LineString
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


r=next(x for x in json.load(open(out/'corrected_rows_context.json')) if x['osm_id']=='w270789165');p=orient(shape(r['geometry']).geoms[0],1);pieces=[]
for label,z0,z1 in [('BASE',0,.15),('UPPER_DECK',2.5,2.7)]:
 vs,fs=extrude(p,z0,z1);pieces.append({'name':label,'vertices':vs,'faces':fs,'material':'STONE'})
coords=list(p.exterior.coords)
for edge,(a,b) in enumerate(zip(coords,coords[1:])):
 dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);d=(dx/L,dy/L);n=(d[1],-d[0]);holes=[];count=max(1,round(L/3))
 for j in range(count):
  c=L*(j+.5)/count;holes.append(box(c-L/count*.38,.55,c+L/count*.38,2.35))
 wall=box(0,.15,L,2.7)
 for h in holes:wall=wall.difference(h)
 def component(label,poly,lo,hi,mat):
  vs,fs=extrude(poly,lo,hi)
  if vs:pieces.append({'name':str(edge)+'_'+label,'vertices':[[a[0]+d[0]*s+n[0]*w,a[1]+d[1]*s+n[1]*w,z] for s,z,w in vs],'faces':fs,'material':mat})
 component('WALL',wall,-.25,0,'STONE')
 for j,h in enumerate(holes):
  x0,z0,x1,z1=h.bounds
  for sign in [-1,1]:
   for k in range(-24,25):
    shift=k*.22;line=LineString([(x0-3,z0+shift-sign*3),(x1+3,z0+shift+sign*(x1-x0+3))]);grid=line.buffer(.022,cap_style=2).intersection(h)
    if not grid.is_empty:component('LATTICE_'+str(j)+'_'+str(sign)+'_'+str(k),grid,-.08,-.025,'LATTICE')
 for j in range(1,18):
  z=.15+j*.14;joint=box(0,z,L,z+.007)
  for h in holes:joint=joint.difference(h.buffer(.025))
  component('BRICK_COURSE_'+str(j),joint,.001,.003,'JOINT')
# Four visible top units represented; unobserved rear machinery is not fabricated.
a=(547.64,617.28);dx,dy=14.91,-3.84;L=math.hypot(dx,dy);ex=(dx/L,dy/L);ey=(ex[1],-ex[0])
for i in range(4):
 x=a[0]+ex[0]*3+ey[0]*(2+i*3.65);y=a[1]+ex[1]*3+ey[1]*(2+i*3.65)
 co=[(x+ex[0]*u+ey[0]*v,y+ex[1]*u+ey[1]*v) for u,v in [(-1.25,-1.25),(1.25,-1.25),(1.25,1.25),(-1.25,1.25)]];vs,fs=extrude(Polygon(co),2.7,4.0);pieces.append({'name':'UNIT_'+str(i),'vertices':vs,'faces':fs,'material':'METAL'})
 # Hollow cylindrical outlet, not a simulated operating fan.
 vs=[];fs=[];N=32
 for radius,z in [(1.12,4.),(1.12,4.8),(.92,4.8),(.92,4.)]:
  vs.extend([[x+radius*math.cos(2*math.pi*k/N),y+radius*math.sin(2*math.pi*k/N),z] for k in range(N)])
 for j in range(4):
  for k in range(N):kn=(k+1)%N;fs.append([j*N+k,j*N+kn,((j+1)%4)*N+kn,((j+1)%4)*N+k])
 pieces.append({'name':'FAN_OUTLET_'+str(i),'vertices':vs,'faces':fs,'material':'FAN'})
for m in pieces:
 edges={}
 for f in m['faces']:
  for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
 assert all(v==2 for v in edges.values()),m['name']
payload={'osm_id':r['osm_id'],'pieces':pieces,'prior_height_m':16.65,'enclosure_height_estimate_m':2.7,'total_height_estimate_m':4.8,'uncertainty_m':1.,'visible_top_units_modeled':4,'source_url':'https://www.google.com/maps/@25.046864,121.5157172,3a,90y,90h,90t/data=!3m4!1e1!3m2!1sGcUP4A8t6LbnYs4aAIOsTQ!2e0','imagery_date':'2025-03','scope':'Low masonry enclosure, red lattice apertures, black upper machinery and pale round outlets observed. Heights, lattice spacing, rear faces, deck and unit dimensions/positions estimated; four visible top units are not a full plant inventory. Does not establish system function or capacity.'};(out/'southwest_plant_photo_payload.json').write_text(json.dumps(payload,ensure_ascii=False));print({'parts':len(pieces),'height':4.8})
