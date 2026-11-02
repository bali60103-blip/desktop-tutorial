import os,json,pathlib,math
from shapely.geometry import shape,box
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'PriorityNodes_20260914';row=next(x for x in json.load(open(root/'CalibrationRound3/corrected_rows_context.json')) if x['osm_id']=='w448227619');g=orient(shape(row['geometry']).geoms[0],1);pieces=[]
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
def add(name,p,z0,z1,mat):
 vs,fs=extrude(p,z0,z1);pieces.append({'name':name,'vertices':vs,'faces':fs,'material':mat})
add('BASE',g,0,.18,'STONE');add('MID_FLOOR',g.buffer(-.3),3.12,3.3,'STONE');add('ROOF',g.buffer(.22),6.0,6.2,'STONE');add('PARAPET',g.difference(g.buffer(-.22)),6.2,6.6,'WALL');add('COPING',g.buffer(.06).difference(g.buffer(-.28)),6.56,6.65,'STONE')
for edge,(a,b) in enumerate(zip(g.exterior.coords,list(g.exterior.coords)[1:])):
 L=math.dist(a,b);d=((b[0]-a[0])/L,(b[1]-a[1])/L);n=(d[1],-d[0]);front=n[0]<-.7 and L>8;rear=n[0]>.7 and L>8;openings=[]
 if front or rear:
  count=max(2,round(L/4.5))
  for j in range(count):
   center=L*(j+.5)/count;w=1.35;openings.append(box(center-w/2,4.15,center+w/2,5.75))
   isdoor=front and j==0;openings.append(box(center-(.85 if isdoor else .675),.18 if isdoor else .85,center+(.85 if isdoor else .675),2.85 if isdoor else 2.5))
 wall=box(0,.18,L,6.)
 for hole in openings:wall=wall.difference(hole)
 def local(name,p,dep0,dep1,mat):
  vv,ff=extrude(p,dep0,dep1);pieces.append({'name':str(edge)+'_'+name,'vertices':[[a[0]+d[0]*s+n[0]*w,a[1]+d[1]*s+n[1]*w,z] for s,z,w in vv],'faces':ff,'material':mat})
 local('WALL',wall,-.3,0,'WALL')
 for i,hole in enumerate(openings):
  x0,z0,x1,z1=hole.bounds;local('RECESSED_PANEL_'+str(i),hole,-.24,-.21,'DARK')
  for j,p in enumerate([box(x0-.07,z0-.07,x0,z1+.07),box(x1,z0-.07,x1+.07,z1+.07),box(x0,z0-.07,x1,z0),box(x0,z1,x1,z1+.07)]):local('FRAME_%d_%d'%(i,j),p,-.02,.035,'STONE')
  if z0>3.5:local('UPPER_MULLION_'+str(i),box((x0+x1)/2-.025,z0,(x0+x1)/2+.025,z1),-.19,-.14,'WOOD')
 for z in [3.05,5.85]:local('CORNICE_'+str(z),box(0,z,L,z+.12),-.02,.26,'STONE')
 if front:local('GROUND_EAVE',box(0,2.98,L,3.1),0,.65,'STONE')
 for z in [.4,.65]:local('PLINTH_COURSE_'+str(z),box(0,z,L,z+.015),.001,.008,'JOINT')
for m in pieces:
 counts={}
 for f in m['faces']:
  for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));counts[k]=counts.get(k,0)+1
 assert all(v==2 for v in counts.values()),m['name']
r={'osm_id':row['osm_id'],'node':'A1 adjacent context','pieces':pieces,'source_url':'https://memory.nhrm.gov.tw/TopicExploration/LocationSpace/Detail/123?viewType=index','evidence':'Official archive exterior photo: two-storey flat-roof station, parapet, eaves, vertically proportioned upper openings and mixed ground doors/windows. OSM footprint retained. 6.65m total and opening positions are estimates; no 2026 as-built condition claimed.','height_estimate_m':6.65,'height_uncertainty_m':1.0,'front_orientation':'west, facing Linsen Road; rear inferred','pending':['Measured facade openings and height','Tree-obscured facade','Current restoration/construction condition','Historical platform registration']};(out/'huashan_station_payload.json').write_text(json.dumps(r,ensure_ascii=False));print({'parts':len(pieces),'height_estimate':6.65})
