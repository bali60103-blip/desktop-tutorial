import bpy,json,pathlib,collections,math
from mathutils import Vector
root=pathlib.Path('/Users/ktlu/Desktop/Civic_Rebuild_20260909_201934/Calibration');sc=bpy.data.scenes['CIVIC_COMPLETE_WORKING_ASSEMBLY'];bpy.context.window.scene=sc;sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();r={'collections':{},'camera_sightlines':[],'ground_issues':[]};foot=[]
for c in sc.collection.children:
 r['collections'][c.name]={'objects':len(c.objects),'render_hidden':sum(o.hide_render for o in c.objects),'viewport_visible':sum(o.visible_get(view_layer=sc.view_layers[0]) for o in c.objects)}
for o in sc.objects:
 if o.type=='MESH' and (any(t in o.name for t in ['_COL_','COLUMN_','PARTITION_','MACHINE','Pier_']) or o.name.startswith('CAL_GROUND_')):
  vv=[list(o.matrix_world@v.co) for v in o.data.vertices];foot.append({'name':o.name,'vertices':vv,'faces':[list(p.vertices) for p in o.data.polygons],'visible':o.visible_get(view_layer=sc.view_layers[0]),'hide_render':o.hide_render})
 if o.type=='MESH' and o.name.startswith('CAL_GROUND_'):
  ec=collections.Counter(tuple(sorted(e)) for p in o.data.polygons for e in p.edge_keys);z=sum(p.area<1e-10 for p in o.data.polygons);non=sum(n!=2 for n in ec.values())
  if z or non:r['ground_issues'].append({'name':o.name,'zero_area':z,'nonmanifold_edges':non})
 if o.type=='CAMERA' and o.name!='FRONTAGE_HEIGHT_CAMERA':
  d=o.matrix_world.to_quaternion()@Vector((0,0,-1));hit,loc,n,idx,obj,m=sc.ray_cast(dg,o.location,d,distance=3000);r['camera_sightlines'].append({'name':o.name,'central_ray_hit':obj.name if hit else None,'distance_m':(loc-o.location).length if hit else None})
(root/'scene_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));(root/'flow_meshes.json').write_text(json.dumps(foot,ensure_ascii=False));result=r['collections']
