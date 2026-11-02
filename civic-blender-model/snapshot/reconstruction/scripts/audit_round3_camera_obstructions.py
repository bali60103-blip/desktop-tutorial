import os
"""Five-ray proximity screening, not a complete visibility or collision certification."""
import bpy,json,pathlib,os,math
from mathutils import Vector
root=pathlib.Path(os.environ['CIVIC_MODEL_ROOT']);out=root/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;deps=bpy.context.evaluated_depsgraph_get();names={r['name'] for r in json.load(open(root/'Calibration/camera_review_index.json'))};rows=[]
for cam in sorted([o for o in sc.objects if o.type=='CAMERA' and o.name in names],key=lambda o:o.name):
 samples=[]
 for dx,dy in [(0,0),(-.2,0),(.2,0),(0,-.15),(0,.15)]:
  direction=(cam.matrix_world.to_quaternion()@Vector((dx,dy,-1))).normalized();hit,loc,norm,face,obj,matrix=sc.ray_cast(deps,cam.matrix_world.translation,direction,distance=40)
  samples.append({'ray':[dx,dy],'distance_m':round((loc-cam.matrix_world.translation).length,3) if hit else None,'object':obj.name if hit else None})
 near=[s for s in samples if s['distance_m'] is not None and s['distance_m']<3];rows.append({'camera':cam.name,'samples':samples,'near_obstruction':len(near)>=3,'recommendation':'Retain station camera; add offset comparison viewpoint after checking pedestrian space' if len(near)>=3 else 'No majority near hit in five rays; full-frame visual review still required'})
r={'method':'Five forward rays within 40m; near flag >=3 hits under 3m. Does not classify image quality or prove free movement. GN instances included through evaluated scene ray casting.','cameras':rows,'near_flag_count':sum(r['near_obstruction'] for r in rows)};(out/'camera_obstruction_audit.json').write_text(json.dumps(r,indent=2));result={'cameras':len(rows),'near_flag_count':r['near_flag_count']}
