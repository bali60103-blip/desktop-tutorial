import bpy,os
from mathutils import Vector
root=os.path.join(os.path.dirname(bpy.data.filepath),'Underbridge_20260922')
working=bpy.data.scenes['CIVIC_UNDERBRIDGE_MASSING_20260916']
paths=[]
for name,x,y in [('UB_YANJI_EQUIPMENT_REVIEW',4538,378),('UB_GUANGFU_SERVICE_REVIEW',4713,410)]:
 s=bpy.data.scenes[name]
 for o in working.objects:
  if o.type!='MESH' or 'MEDIAN_WORKING' not in o.name:continue
  p=[o.matrix_world@Vector(v) for v in o.bound_box]
  if max(v.x for v in p)>x-45 and min(v.x for v in p)<x+45 and o.name not in s.objects:s.collection.objects.link(o)
 c=s.camera;c.location=(x-20,y+50,30);c.rotation_euler=(Vector((x,y,1))-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=65
 s.render.filepath=os.path.join(root,name+'_NORTH_FINAL.png');bpy.ops.render.render(write_still=True,scene=s.name);paths.append(s.render.filepath)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'renders':paths}
