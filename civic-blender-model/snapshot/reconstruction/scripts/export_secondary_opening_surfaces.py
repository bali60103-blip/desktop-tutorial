import bpy,json,pathlib
out=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Calibration');dg=bpy.context.evaluated_depsgraph_get();rows=[]
for name in ['GROUND_CURBS_WITH_ESTIMATED_OPENINGS','GROUND_CROSSWALK_MARKINGS_ESTIMATED']:
 o=bpy.data.objects[name];e=o.evaluated_get(dg);m=e.to_mesh();rows.append({'name':name,'vertices':[list(o.matrix_world@v.co) for v in m.vertices],'faces':[list(p.vertices) for p in m.polygons]});e.to_mesh_clear()
(out/'secondary_opening_surfaces.json').write_text(json.dumps(rows));result={'surfaces':len(rows)}
