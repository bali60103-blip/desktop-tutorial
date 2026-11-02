import bpy,json,pathlib,os
from mathutils import Vector
sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';rows=[]
for o in sc.objects:
 if o.type!='MESH' or not o.visible_get() or len(o.data.vertices)>100000:continue
 if not any(any(t in c.name for t in ['PARKING','WORKSHEET04','COMPLETION_GROUND_HIGHWAY']) for c in o.users_collection):continue
 for p in o.data.polygons:
  vs=[o.matrix_world@o.data.vertices[i].co for i in p.vertices];zs=[v.z for v in vs]
  if max(zs)-min(zs)<.005 and min(zs)<-1 and max(zs)>-8 and abs((o.matrix_world.to_3x3()@p.normal).z)>.9:
   rows.append({'object':o.name,'face':p.index,'z':sum(zs)/len(zs),'xy':[[v.x,v.y] for v in vs]})
(out/'parking_horizontal_faces.json').write_text(json.dumps(rows));result={'faces':len(rows)}
