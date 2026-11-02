import bpy,os,pathlib,json
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;sc.view_layers[0].update();rows=[]
for o in bpy.data.collections['COMPLETION_EQUIPMENT'].objects:
 bb=[list(o.matrix_world@Vector(v)) for v in o.bound_box];rows.append({'name':o.name,'bounds':bb,'dimensions':list(o.dimensions),'location':list(o.location),'rotation':list(o.rotation_euler),'properties':{k:str(o[k]) for k in o.keys()}})
(out/'equipment_detail_inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));result={'objects':[{'name':r['name'],'dimensions':r['dimensions'],'properties':r['properties']} for r in rows]}
