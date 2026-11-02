import bpy,os
from mathutils import Vector
s=bpy.data.scenes.new('UB_STATION_006_010_REVIEW');s.collection.children.link(bpy.data.collections['UB_STATION_006_010'])
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 if o.name=='UB_MEDIAN_0_WITH_STATION_UTURN_EST' or (o.name.startswith('CAL_GROUND_MEDIAN_WORKING_ESTIMATED_') and o.name.rsplit('_',1)[-1] in ['0','2']):s.collection.objects.link(o)
 elif o.name.startswith('UNVERIFIED_Pier_'):
  p=[o.matrix_world@Vector(v) for v in o.bound_box];x=sum(v.x for v in p)/8
  if 600<x<1150:s.collection.objects.link(o)
 elif o.name.startswith('COMP_ACCESS_公中'):s.collection.objects.link(o)
cam=bpy.data.objects.new('UB_STATION_REVIEW_CAMERA',bpy.data.cameras.new('UB_STATION_REVIEW_CAMERA'));s.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.ortho_scale=115;s.camera=cam
sun=bpy.data.objects.new('UB_STATION_REVIEW_SUN',bpy.data.lights.new('UB_STATION_REVIEW_SUN','SUN'));s.collection.objects.link(sun);sun.data.energy=3;sun.rotation_euler=(.5,-.6,.3)
s.world=bpy.data.worlds.get('UB_ZZ_REVIEW_WORLD');s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922');paths=[]
for tag,x,y in [('WEST',673,812),('CENTRAL',798,790),('EAST',992,753),('UTURN',854,780)]:
 cam.location=(x+20,y-85,85);cam.rotation_euler=(Vector((x,y,0))-cam.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=os.path.join(root,'STATION_'+tag+'_REVIEW.png');bpy.ops.render.render(write_still=True,scene=s.name);paths.append(s.render.filepath)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'renders':paths}
