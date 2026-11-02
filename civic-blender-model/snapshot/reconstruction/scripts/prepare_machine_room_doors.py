import json,os,pathlib,math
from shapely.geometry import Polygon,LineString
from shapely.ops import unary_union
from shapely.affinity import affine_transform
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';rows=json.load(open(out/'machine_room_existing_walls.json'));payload=[]
for r in rows:
 vs=r['vertices'];z0=min(v[2] for v in vs);z1=max(v[2] for v in vs);g=unary_union([Polygon([vs[i][:2] for i in p]) for p in r['faces'] if all(abs(vs[i][2]-z1)<.001 for i in p)]);rect=g.minimum_rotated_rectangle;coords=list(rect.exterior.coords)[:-1];cx,cy=rect.centroid.coords[0];options=[]
 for a,b in zip(coords,coords[1:]+coords[:1]):
  ex,ey=b[0]-a[0],b[1]-a[1];l=math.hypot(ex,ey);f=[ey/l,-ex/l]
  if f[0]*((a[0]+b[0])/2-cx)+f[1]*((a[1]+b[1])/2-cy)<0:f=[-x for x in f]
  u=[f[1],-f[0]];local=affine_transform(g,[u[0],u[1],f[0],f[1],-cx*u[0]-cy*u[1],-cx*f[0]-cy*f[1]]);x0,y0,x1,y1=local.bounds;line=LineString([(x0+.2,y1-.075),(x1-.2,y1-.075)]);gap=line.difference(local)
  pieces=list(gap.geoms) if hasattr(gap,'geoms') else [gap]
  for piece in pieces:
   if piece.geom_type=='LineString' and .5<piece.length<2:options.append({'u':u,'f':f,'front_y':y1,'door_left':piece.bounds[0],'door_right':piece.bounds[2],'existing_gap_width_m':piece.length,'width_m':x1-x0,'depth_m':y1-y0})
 assert len(options)==1,(r['name'],options)
 payload.append({'source':r['name'],'origin':[cx,cy,z0],'floor_z':z0,'top_z':z1,**options[0],'door_height_assumed_m':2.1,'status':'Door position follows existing estimated full-height wall gap; 2.1m head height inferred, no survey claim'})
(out/'machine_room_door_payload.json').write_text(json.dumps(payload,indent=2));print({'rooms':len(payload),'gap_width_range':[min(r['existing_gap_width_m'] for r in payload),max(r['existing_gap_width_m'] for r in payload)]})
