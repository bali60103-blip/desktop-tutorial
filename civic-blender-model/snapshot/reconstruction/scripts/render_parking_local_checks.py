"""Render local parking ramp checks and expose the overlap as a QA marker."""
import bpy,json,pathlib
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'ParkingSections';sc=bpy.data.scenes['PARKING_SECTIONS_COMPARISON'];col=bpy.data.collections['PARKING_8_SECTIONS_COMPARISON_ASSUMED']
records=json.load(open('/tmp/civic-parking-segments/sections.json'))['sections'];main=bpy.data.scenes['Scene']
for r in records:
 cam=bpy.data.objects.get(r['name']+'_B1_B2_CAMERA')
 if not cam:continue
 sc.camera=cam;sc.render.resolution_x=1400;sc.render.resolution_y=800;sc.render.filepath=str(out/(r['name']+'_ramp_check.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
# Plan overview camera for the known overlap; do not move either assumption.
a=next(r for r in records if r['name']=='延吉');p=Vector((*a['axis_live'][len(a['axis_live'])//2],0))
cu=bpy.data.curves.new('QA_DUNYAN_YANJI_OVERLAP','CURVE');cu.dimensions='3D';cu.bevel_depth=.25;sp=cu.splines.new('POLY');sp.points.add(4)
for v,q in zip(sp.points,[(-100,-15),(0,-15),(0,15),(-100,15),(-100,-15)]):v.co=(p.x+q[0],p.y+q[1],.5,1)
mat=bpy.data.materials.new('QA_OVERLAP_RED');mat.diffuse_color=(1,.04,.03,1);cu.materials.append(mat);o=bpy.data.objects.new(cu.name,cu);col.objects.link(o);o['status']='Approximate review marker for estimated envelope overlap, not exact intersection or physical structure'
cam=bpy.data.objects['PARKING_OVERVIEW'];sc.camera=cam;cam.location=p+Vector((0,-100,150));cam.rotation_euler=(p-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=260;sc.render.filepath=str(out/'yanji_overlap_review.png');bpy.ops.render.render(write_still=True,scene=sc.name)
bpy.context.window.scene=main;bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'file':bpy.data.filepath,'local_ramp_previews':6,'overlap_review_marker_added':True}
