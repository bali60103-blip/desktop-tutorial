import bpy,json,pathlib
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934');out=root/'Calibration';sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];sc.view_layers[0].update();rows=[];cams=[]
for o in sc.objects:
 if o.type=='MESH' and (o.name.startswith(('DECK_','RAMP_','GROUND_','COMP_ACCESS_','COMP_MEDIAN_','COMP_OSM_EQUIP_')) or o.name.startswith('UNVERIFIED_Pier_')):
  rows.append({'name':o.name,'vertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'faces':[list(f.vertices) for f in o.data.polygons],'properties':{k:str(o[k]) for k in o.keys()}})
 if o.type=='CAMERA':cams.append({'name':o.name,'location':list(o.matrix_world.translation),'direction':list(o.matrix_world.to_quaternion()@Vector((0,0,-1))),'lens':o.data.lens,'sensor_width':o.data.sensor_width,'sensor_fit':o.data.sensor_fit})
r={'file':bpy.data.filepath,'meshes':rows,'cameras':cams};(out/'model_geometry.json').write_text(json.dumps(r,ensure_ascii=False));result={'file':r['file'],'meshes':len(rows),'cameras':len(cams)}
