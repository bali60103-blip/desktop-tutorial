import bpy,os
from mathutils import Vector
s=bpy.data.scenes.new('UB_GUANGHUA_REVIEW')
for n in ['UB_GUANGHUA_021_022_EST','UB_GUANGHUA_MEDIAN_COMPARISON_EST']:s.collection.children.link(bpy.data.collections[n])
for o in bpy.data.scenes['CIVIC_UNDERBRIDGE_MASSING_20260916'].objects:
 if o.type!='MESH':continue
 p=[o.matrix_world@Vector(v) for v in o.bound_box];x=sum(v.x for v in p)/8
 if 2050<x<2250 and any(k in o.name for k in ['MEDIAN_WORKING','COMP_ACCESS','VENT_DETAIL','COMP_MEDIAN','UB_LINSEN','Pier_']):s.collection.objects.link(o)
cam=bpy.data.objects.new('UB_LAND_REVIEW_CAMERA',bpy.data.cameras.new('UB_LAND_REVIEW_CAMERA'));s.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.ortho_scale=190;s.camera=cam
sun=bpy.data.objects.new('UB_LAND_REVIEW_SUN',bpy.data.lights.new('UB_LAND_REVIEW_SUN','SUN'));s.collection.objects.link(sun);sun.data.energy=3;sun.rotation_euler=(.5,-.6,.3)
s.world=bpy.data.worlds.get('UB_ZZ_REVIEW_WORLD');s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922');paths=[]
for tag,x,y in [('GUANGHUA',2150,503)]:
 cam.location=(x+20,y-120,125);cam.rotation_euler=(Vector((x,y,0))-cam.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=os.path.join(root,'LANDSCAPE_'+tag+'_REVIEW.png');bpy.ops.render.render(write_still=True,scene=s.name);paths.append(s.render.filepath)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'renders':paths}
