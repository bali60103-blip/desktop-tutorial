"""Virtual side viewpoints facing the derived boulevard axis; positions are not surveyed sidewalks."""
import json,pathlib,os,math
from shapely.geometry import shape,Point,LineString,Polygon
from shapely import STRtree
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';st=json.load(open(root/'Cameras_200m/camera_stations.json'))['stations'];rows=json.load(open(out/'corrected_rows_context.json'));geoms=[shape(r['geometry']).buffer(.75) for r in rows if r['base_z_m']<2.2 and r['height_m']>1.2]
e=json.load(open(out/'jingfu_evidence.json'));geoms.append(Polygon(e['live_polygons']['roof']).buffer(1));tree=STRtree(geoms);payload=[]
for i,s in enumerate(st):
 a=st[max(0,i-1)]['live_xy'];b=st[min(len(st)-1,i+1)]['live_xy'];dx,dy=b[0]-a[0],b[1]-a[1];d=math.hypot(dx,dy);t=[dx/d,dy/d];n=[-t[1],t[0]];q=s['live_xy']
 for side,sgn in [('N',1),('S',-1)]:
  options=[]
  for lateral in [18,16,20,14,22,12,24,10,26,8,28,6,30,4]:
   for along in [0,-4,4,-8,8,-12,12,-20,20,-30,30]:
    p=Point(q[0]+n[0]*lateral*sgn+t[0]*along,q[1]+n[1]*lateral*sgn+t[1]*along)
    if len(tree.query(p,predicate='intersects')):continue
    sight=LineString([p.coords[0],q]);blocked=len(tree.query(sight,predicate='intersects'));score=abs(lateral-18)+abs(along)*.7+blocked*100;options.append((score,lateral,along,p,blocked))
  assert options,('No exterior candidate',s['label'],side)
  score,lateral,along,p,blocked=min(options,key=lambda x:x[0]);payload.append({'camera':'CIVIC200_'+s['label']+'_'+side,'station':s['label'],'side_position':side,'xy':list(p.coords[0]),'axis_xy':q,'lateral_offset_m':sgn*lateral,'along_offset_m':along,'footprint_sight_obstructions':blocked,'status':'Estimated virtual side viewpoint; 0.75m footprint buffer, no claim of sidewalk or pedestrian access verification'})
r={'method':'53 stations; paired north/south side viewpoints looking at each original axis station. Prefer 18m lateral offset and zero along offset, avoid low building footprints. Search 4-30m lateral and up to30m along. Axis itself is a derived OSM analysis axis, not surveyed engineering centerline.','cameras':payload};(out/'inward_camera_payload.json').write_text(json.dumps(r,indent=2));print({'cameras':len(payload),'blocked_sightlines':sum(p['footprint_sight_obstructions']>0 for p in payload),'along_adjusted':sum(p['along_offset_m']!=0 for p in payload),'min_lateral':min(abs(p['lateral_offset_m']) for p in payload),'max_lateral':max(abs(p['lateral_offset_m']) for p in payload)})
