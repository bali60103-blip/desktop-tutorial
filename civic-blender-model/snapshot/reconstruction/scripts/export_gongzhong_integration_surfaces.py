import bpy,os,json,pathlib
from mathutils import Vector
out=pathlib.Path(os.environ['CIVIC_MODEL_ROOT'])/'CalibrationRound3';sc=bpy.data.scenes['CIVIC_BLOCKS_FACADES_WORKING'];bpy.context.window.scene=sc;lc=sc.view_layers[0].layer_collection.children['COMPLETION_REMOVABLE_ROOFS'];old=lc.exclude;lc.exclude=False;sc.view_layers[0].update();case=json.load(open(out/'core_integration_search.json'))['cases'][0];rows=[]
try:
 for name in case['requires_opening_updates']:
  o=bpy.data.objects[name];vs=[list(o.matrix_world@v.co) for v in o.data.vertices];rows.append({'name':name,'vertices':vs,'faces':[list(p.vertices) for p in o.data.polygons],'z_levels':sorted(set(round(v[2],5) for v in vs))})
finally:lc.exclude=old;sc.view_layers[0].update()
(out/'gongzhong_integration_surfaces.json').write_text(json.dumps(rows));result={'surfaces':[{k:v for k,v in r.items() if k not in ['vertices','faces']} for r in rows]}
