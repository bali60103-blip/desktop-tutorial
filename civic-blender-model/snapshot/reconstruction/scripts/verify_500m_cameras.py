"""Verify camera rig and render a full low-resolution review set without altering camera choices."""
import bpy,json,pathlib,math
from mathutils import Vector
root=pathlib.Path(ROOT);sc=bpy.context.scene;p=json.loads((root/'camera_build_check.json').read_text());before={'frame':sc.frame_current,'camera':sc.camera,'x':sc.render.resolution_x,'y':sc.render.resolution_y,'percentage':sc.render.resolution_percentage,'filepath':sc.render.filepath,'engine':sc.render.engine};checks=[];renders=[]
try:
 sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.color_type='MATERIAL';sc.render.resolution_x=960;sc.render.resolution_y=540;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
 for r in p['cameras']:
  o=bpy.data.objects[r['camera']];forward=o.rotation_euler.to_quaternion()@Vector((0,0,-1));expected=Vector(r['direction']);dot=forward.dot(expected)
  assert dot>.99999,(o.name,dot)
  checks.append({'camera':o.name,'direction_dot':dot,'pitch_error':abs(forward.z)})
  sc.frame_set(r['timeline_frame']);sc.camera=o;sc.render.filepath=str(root/(o.name+'.png'));bpy.ops.render.render(write_still=True);renders.append(sc.render.filepath)
finally:
 sc.frame_set(before['frame']);sc.camera=before['camera'];sc.render.resolution_x=before['x'];sc.render.resolution_y=before['y'];sc.render.resolution_percentage=before['percentage'];sc.render.filepath=before['filepath'];sc.render.engine=before['engine']
pairs={}
for r in p['cameras']:pairs.setdefault(r['chainage_m'],[]).append(r)
for station,rs in pairs.items():
 assert len(rs)==2
 assert Vector(rs[0]['position'])==Vector(rs[1]['position'])
 assert Vector(rs[0]['direction']).dot(Vector(rs[1]['direction']))<-.99999
regular=sorted(s for s in pairs if abs(s%500)<1e-6)
assert all(abs(b-a-500)<1e-6 for a,b in zip(regular,regular[1:]))
result={'file':bpy.data.filepath,'verified_cameras':len(checks),'verified_pairs':len(pairs),'regular_station_count':len(regular),'endpoint_extra':True,'orientation_checks_passed':True,'surface_fallback_cameras':[r['camera'] for r in p['cameras'] if not r['modeled_surface_hit']],'pier_obstruction_cameras':[{'camera':r['camera'],'distance_m':r['pier_obstruction_within_30m']} for r in p['cameras'] if r['pier_obstruction_within_30m'] is not None],'renders':renders};(root/'camera_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
