import bpy,json,pathlib
from mathutils import Vector
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Calibration');sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];bpy.context.window.scene=sc;sc.view_layers[0].update();deps=bpy.context.evaluated_depsgraph_get();rows=[]
for name in ['GROUND_ROADS_OFFICIAL_XY','GROUND_ROADS_ESTIMATED_GAPS','GROUND_SIDEWALKS_WITH_ESTIMATED_RAMPS','GROUND_MEDIAN_WORKING_ESTIMATED']:
 o=bpy.data.objects[name];eo=o.evaluated_get(deps);me=eo.to_mesh();rows.append({'name':name,'vertices':[list(o.matrix_world@v.co) for v in me.vertices],'faces':[list(f.vertices) for f in me.polygons]});eo.to_mesh_clear()
(out/'evaluated_ground.json').write_text(json.dumps(rows));result={'surfaces':len(rows)}
