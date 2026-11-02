"""Photo-informed Huashan ventilation building, with explicitly estimated heights."""
import json,os,pathlib,math
from shapely.geometry import shape,box,Polygon
from shapely.geometry.polygon import orient
from shapely import constrained_delaunay_triangles
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';r=next(x for x in json.load(open(out/'corrected_rows_context.json')) if x['osm_id']=='w268396843');g=shape(r['geometry']);pieces=[]
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
for label,clip,height in [('WEST',box(1400,500,1506.6,600),7.2),('EAST',box(1506.6,500,1600,600),4.2)]:
 p=orient(g.intersection(clip),1)
 for name,poly,z0,z1,mat in [('PLINTH',p,0,1.0,'BASE'),('ROOF',p.buffer(.18),height-.3,height,'BASE')]:
  vs,fs=extrude(poly,z0,z1);pieces.append({'name':label+'_'+name,'vertices':vs,'faces':fs,'material':mat})
 coords=list(p.exterior.coords)
 for edge,(a,b) in enumerate(zip(coords,coords[1:])):
  dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);d=(dx/L,dy/L);n=(d[1],-d[0]);front=(a[1]+b[1])/2<535 and L>10
  openings=[]
  if front and label=='WEST':
   for c in [.42,.65]:openings.append(box(c*L-1.5,1.15,c*L+1.5,height-.55))
  wall=box(0,1.,L,height-.3)
  for hole in openings:wall=wall.difference(hole)
  vs,fs=extrude(wall,-.25,0)
  vs=[[a[0]+d[0]*s+n[0]*w,a[1]+d[1]*s+n[1]*w,z] for s,z,w in vs]
  pieces.append({'name':label+'_WALL_'+str(edge),'vertices':vs,'faces':fs,'material':'STONE'})
  for hi,hole in enumerate(openings):
   x0,z0,x1,z1=hole.bounds
   # Real geometric openings: thin recessed louver blades plus frame members.
   for j in range(math.floor((z1-z0)/.14)):
    z=z0+.10+j*.14;vv,ff=extrude(box(x0+.06,z,x1-.06,z+.055),-.13,-.04);vv=[[a[0]+d[0]*s+n[0]*w,a[1]+d[1]*s+n[1]*w,h] for s,h,w in vv];pieces.append({'name':label+'_LOUVER_'+str(hi)+'_'+str(j),'vertices':vv,'faces':ff,'material':'METAL'})
   frames=[box(x0-.06,z0,x0+.06,z1),box(x1-.06,z0,x1+.06,z1),box(x0,z0-.06,x1,z0+.06),box(x0,z1-.06,x1,z1+.06),box((x0+x1)/2-.04,z0,(x0+x1)/2+.04,z1),box(x0,(z0+z1)/2-.04,x1,(z0+z1)/2+.04)]
   for j,frame in enumerate(frames):
    vv,ff=extrude(frame,-.02,.08);vv=[[a[0]+d[0]*s+n[0]*w,a[1]+d[1]*s+n[1]*w,h] for s,h,w in vv];pieces.append({'name':label+'_FRAME_'+str(hi)+'_'+str(j),'vertices':vv,'faces':ff,'material':'STONE'})
  # Thin joint strips express observed stone coursing, not exact tile dimensions.
  for j in range(1,math.floor((height-1)/.75)):
   joints=box(0,1+j*.75-.007,L,1+j*.75+.007)
   for hole in openings:joints=joints.difference(hole.buffer(.07))
   vv,ff=extrude(joints,.001,.004)
   if vv:pieces.append({'name':label+'_JOINT_'+str(edge)+'_'+str(j),'vertices':[[a[0]+d[0]*s+n[0]*w,a[1]+d[1]*s+n[1]*w,h] for s,h,w in vv],'faces':ff,'material':'JOINT'})
for m in pieces:
 edges={}
 for f in m['faces']:
  for a,b in zip(f,f[1:]+f[:1]):k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
 assert all(v==2 for v in edges.values()),m['name']
payload={'osm_id':r['osm_id'],'pieces':pieces,'height_estimates_m':{'west':7.2,'east':4.2},'height_uncertainty_m':{'west':1.5,'east':1.0},'prior_height_m':26.4,'source_url':'https://www.google.com/maps/@25.0461261,121.5252466,3a,90y,90t/data=!3m4!1e1!3m2!1sT78R49HGwsDyTL67zIdmow!2e0','imagery_date':'2019-08','scope':'Photo-informed comparison: stepped low building, grey stone walls, reddish plinth/cornice and localized metal louvers observed. Heights, split location, opening sizes, unobserved rear walls and stone coursing estimated; no survey or 2026 condition verification.'};(out/'huashan_photo_shell_payload.json').write_text(json.dumps(payload,ensure_ascii=False));print({'pieces':len(pieces),'heights':payload['height_estimates_m']})
