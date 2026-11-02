import bpy,json,pathlib,os,datetime,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;payload=json.load(open(out/'inward_camera_payload.json'));before={};stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');bpy.ops.wm.save_as_mainfile(filepath=str(out/('BEFORE_INWARD_APPLY_'+stamp+'.blend')),copy=True)
markers=[(m.name,m.frame,m.camera.name if m.camera else None) for m in sc.timeline_markers];frame_range=(sc.frame_start,sc.frame_end);vs=[];fs=[]
for o in sc.objects:
 if o.type=='MESH' and o.visible_get() and o.name.startswith(('CAL_GROUND_ROADS_','CAL_GROUND_SIDEWALKS_','GROUND_MEDIAN_','CAL_GROUND_MEDIAN_')):
  off=len(vs);vs.extend([o.matrix_world@v.co for v in o.data.vertices]);fs.extend([[off+i for i in p.vertices] for p in o.data.polygons])
ground=BVHTree.FromPolygons(vs,fs)
def z_at(xy):
 hit,_,_,_=ground.ray_cast(Vector((*xy,3)),Vector((0,0,-1)),8);return (hit.z,True) if hit is not None else (0.,False)
checks=[]
for r in payload['cameras']:
 o=bpy.data.objects[r['camera']];before[o.name]={'location':list(o.location),'rotation_euler':list(o.rotation_euler),'direction':o.get('direction')};z,hit=z_at(r['xy']);tz,thit=z_at(r['axis_xy']);target=Vector((*r['axis_xy'],tz+.1));o.location=(*r['xy'],z+1.7);direction=target-o.location;o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();o['direction']='TOWARD_BOULEVARD_AXIS';o['camera_side']=r['side_position'];o['axis_target']=list(target);o['position_status']=r['status'];o['lateral_offset_m']=r['lateral_offset_m'];o['along_offset_m']=r['along_offset_m'];o['surface_hit']=hit;o['height_above_modeled_surface_m']=1.7
 actual=o.rotation_euler.to_quaternion()@Vector((0,0,-1));error=math.degrees(actual.angle(direction));assert error<.05,(o.name,error);checks.append({'camera':o.name,'position':list(o.location),'axis_target':list(target),'aim_error_degrees':error,'surface_hit':hit,'axis_surface_hit':thit})
sc.view_layers[0].update();deps=bpy.context.evaluated_depsgraph_get()
for r in checks:
 o=bpy.data.objects[r['camera']];v=Vector(r['axis_target'])-o.location;hit,p,_,_,obj,_=sc.ray_cast(deps,o.location,v.normalized(),distance=v.length)
 r['sight_hit_object']=obj.name if hit else None;r['sight_hit_distance_m']=(p-o.location).length if hit else None
assert markers==[(m.name,m.frame,m.camera.name if m.camera else None) for m in sc.timeline_markers];assert frame_range==(sc.frame_start,sc.frame_end)
sc['camera_animation']='East to west, north-side then south-side at each station, both facing the boulevard axis, 1 second each, 24fps.';sc.frame_set(1)
r={'cameras':len(checks),'animation_unchanged':True,'fps':sc.render.fps,'frames':list(frame_range),'camera_height_m':1.7,'target_height_above_axis_surface_m':.1,'previous_transforms':before,'checks':checks,'note':'Names ending N/S now identify camera side, not viewing direction. Positions and analysis axis remain estimated; some piers may occlude inward views.'};(out/'inward_camera_check.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);result={'cameras':len(checks),'max_aim_error_degrees':max(x['aim_error_degrees'] for x in checks),'ground_misses':sum(not x['surface_hit'] for x in checks),'sight_occlusions':sum(x['sight_hit_object'] is not None for x in checks),'animation_unchanged':True}
